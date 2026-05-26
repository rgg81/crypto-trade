---
iteration: iter-v1/020
date: 2026-05-26
verdict: EXPLORATION-NEGATIVE
subtype: Catastrophic-NEGATIVE (Section 8 Row 6 — F1 OOS Sharpe Δ -0.86 ≤ -0.55 threshold; H_INTRINSIC REFUTED at training-time granularity per LM Master Phase 7.4 §3)
axis_family: per-cohort-specialization-BTC (NEW 11th family — FIRST usage at v1 catalog level; THIRD per-cohort EXPLORATION under USER STRATEGIC PIVOT after LINK /018 + ETH+gate /019)
cohort: BTC (single-symbol cohort, Model H exclusive dispatch via V1_ITER020_UNIVERSE=(BTCUSDT,))
specialization: NONE — pure single-cohort isolation; NO gate, NO new feature, NO new labeling (cycle-3 #5 CONTROL EXPERIMENT for per-cohort methodology — tests whether isolation ALONE can restructure asymmetric IS-OOS rotation)
cadence_position: cycle-3 EXPLORATION (#5 of 10)
anchor: v0.v1-baseline-corrected (BASELINE_V1.md commit f8bc12c) — UNCHANGED
merge_decision: NO-MERGE (EXPLORATION-NEGATIVE Catastrophic; BTC-only Model H specialist EXCLUDED from /027 substrate; BTC enters /027 IN POOL via Model A; BASELINE_V1.md UPDATE NOT triggered — only CONFIRMATION-MERGE updates baseline per `feedback_v3_baseline_update_policy.md`)
---

# Iteration iter-v1/020 — Diary

## Decision: NO-MERGE (BTC-only Model H specialist EXCLUDED from /027 substrate; BTC enters /027 IN POOL)

**EXPLORATION-NEGATIVE Catastrophic-NEGATIVE** (Section 8 Row 6). BTC-only single-symbol cohort dispatch through Model H + pure isolation (NO gate, NO new feature, NO new labeling — mirroring Model A's BTC+ETH pool config of `atr_tp=2.9, atr_sl=1.45, apply_r1=False`) **DISSOLVED BTC's pool-conferred OOS positive rotation** at single-seed EXPLORATION budget. OOS Sharpe **−0.5566** (annualized daily; comparison.csv) / **F1 OOS Sharpe Δ −0.86** vs BTC-in-pool monthly Sharpe proxy +0.30 anchor / **OOS net PnL −10.17%** (compared to baseline BTC-in-pool +33.17%, Δ −43.34pp) / 53 OOS trades / **F-AXIS-MECHANISM #1/2/4 PASS, #3 BORDERLINE PASS** / **Jaccard 0.084 combined** (IS 0.098 / OOS 0.048) confirms NEW signal source via basin relocation BUT INTO structurally adverse OOS subset. BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`). **BTC-only Model H specialist EXCLUDED from /027 substrate**; BTC enters /027 IN POOL via Model A (no architectural change vs baseline for BTC). **/021 advances to methodology pivot** per Critic Phase 7.5 Path Forward #1 + LM Master Phase 7.4 §5 hybrid Option C + B convergent recommendation.

## One-Line Outcome

At v1 EXPLORATION budget (ENSEMBLE_SIZE=3 + n_trials=18 + V1_FEATURE_COLUMNS_PRUNED 40 + BTC-only universe via `V1_ITER020_UNIVERSE = (BTCUSDT,)` + 8h candles + `abs_pnl` weighting + Model H exclusive dispatch + R3 only + ATR×2.9 TP / ATR×1.45 SL mirroring Model A's BTC+ETH pool semantics + R5 disabled + NO gate, NO new feature, NO new labeling — pure cohort isolation control experiment) BTC-only single-symbol cohort produced **IS Sharpe −0.5914** (Δ **−0.4714** Catastrophic-NEGATIVE F3 band vs BTC-in-pool IS Sharpe proxy −0.12; F3 fires Catastrophic-NEGATIVE) + **OOS Sharpe −0.5566** (Δ **−0.8566** Catastrophic-NEGATIVE F1 band vs BTC-in-pool OOS Sharpe proxy +0.30; F1 fires Section 8 Row 6 decisively) + **OOS net PnL −10.17%** (Δ vs baseline BTC-in-pool +33.17% = −43.34pp; one of largest cycle-3 per-symbol OOS swings) + **OOS WR 45.3%** (vs BTC-in-pool ~45.7%; same WR, very different Sharpe — explained by per-trade variance + drawdown clustering in 2025-04 / 2025-12 / 2026-02 months) + **F-AXIS-MECHANISM #1 binary PASS** (per_symbol.csv 100% BTCUSDT IS+OOS; Model H exclusive dispatch via V1_ITER020_UNIVERSE guard worked cleanly) + **F-AXIS-MECHANISM #2 trade-count PASS at QR blocking band** (IS 122 ∈ [70, 150] / OOS 53 ∈ [25, 55]; OOS 53 BREACH-HIGH +7 vs LM Master tighter sub-band [25, 46] — INFORMATIONAL per /019 framework, does NOT trigger F-AXIS #2 BREACH) + **F-AXIS-MECHANISM #3 BORDERLINE PASS** (IS_H1 net_pnl computed at engineering_report.md §3 = **−21.95%** inside band [−45%, −15%] near upper boundary; resolved from Critic Phase 7.5 INDETERMINATE status; regime-bound IS catastrophic CHARACTER preserved with Δ +14.06pp vs baseline IS_H1 = −36.01%) + **F-AXIS-MECHANISM #4 n_eff_per_cell = 9 PASS exact** (matches LM Master point estimate; /019 §5 methodology calibration accurate) + **PSR_monthly_vs_0 OOS = 0.301** (below PROMISING-INERT floor 0.40, above Catastrophic floor 0.10 — Δ-based Catastrophic verdict per brief Section 8 Row 6 supersedes PSR-based read) + **PSR_monthly_vs_1 OOS = 0.038** (3.8% probability OOS Sharpe ≥ 1.0 at observed parameters) + **Jaccard 0.084 vs baseline BTC roster** (combined kept IS+OOS — 25 overlapping `open_time` rows out of union 298; IS 0.098 / OOS 0.048; **REFUTES LM Master Phase 4.5 §4 prediction [0.10, 0.25] in alternative-branch direction**; matches /018+/019 ≈ 0.04 pattern — pool independence claim at training-time is at higher-than-monthly granularity per LM Master Phase 7.4 §3) + **wall-clock ~25 min** (87% margin against 2h cap; identical scale to /018 and /019) — verdict-class cell **NEGATIVE-CATASTROPHIC** (Section 8 Row 6 robust across 4 anchor frames per Critic Phase 7.5 anchor-frame audit); Critic + LM Master CONVERGE on EXPLORATION-NEGATIVE Catastrophic; BTC-only Model H specialist EXCLUDED from /027 substrate; **/021 axis advances per convergent recommendation: methodology pivot — add `_write_feature_importance` per /019 §6 + add training-time pool-anchor diagnostic** (per-fold Optuna best-trial parameter delta between BTC-in-pool Model A and BTC-only Model H at SAME seed=42 to predict LTC + DOT pool-anchor signature BEFORE wall-clock spend).

## What Worked (process-level)

### F-AXIS-MECHANISM #1 binary PASS clean (cohort isolation dispatch correct)

per_symbol.csv contains 100% BTCUSDT both IS (122 trades) and OOS (53 trades). Model H exclusive dispatch via `V1_ITER020_UNIVERSE = (BTCUSDT,)` and `set(symbols)==set(V1_ITER020_UNIVERSE)` guard functioned cleanly. Zero spillover from Model A/C/D/E/F/G dispatch branches. **Mechanical implementation correct** — the Catastrophic verdict is NOT a dispatch defect; it is the structural outcome of pure isolation against a pool-conferred edge.

### F-AXIS-MECHANISM #4 n_eff_per_cell PASS exact (methodology calibration accurate)

LM Master Phase 4.5 §3 predicted n_eff_per_cell point estimate **9** ∈ [7, 10] band based on training row count (BTC-only ≈ 113-130 IS labels). Observed n_eff_per_cell = **9** exact — methodology calibration from /019 §5 update (n_eff predicted from training row count, NOT post-hoc kept trades) holds. Matches /018 LINK-only (n_eff = 9). **The ONE Phase 4.5 prediction that landed cleanly** per LM Master Phase 7.4 §6.

### F-AXIS-MECHANISM #3 BORDERLINE PASS — IS regime constraint partial

Computed at engineering_report.md §3: IS_H1 net_pnl = **−21.95%** inside band [−45%, −15%] near upper boundary. BTC-only Optuna trajectory DID partially escape IS_H1 catastrophic magnitude (Δ +14.06pp vs baseline IS_H1 = −36.01%) but did NOT dissolve it. **Regime-bound IS catastrophic CHARACTER preserved** at single-cohort isolation — Section 0.4 EDA framing was correct on the regime-binding test specifically. The Catastrophic verdict at F1 is NOT a regime-bound IS issue; it is a pool-conferred OOS issue.

### Critic + LM Master CONVERGE on EXPLORATION-NEGATIVE Catastrophic

Both Critic Phase 7.5 (`review.md` HEAD `ebdc4a6`) and LM Master Phase 7.4 (`lgbm_advisor.md`) converge on **Section 8 Row 6 (F1 Δ ≤ −0.55) → NEGATIVE-CATASTROPHIC**. Verdict ROBUST across 4 anchor frames (3 of 4 land Catastrophic; net_pnl trade-sum frame lands NEGATIVE band only at Δ −33pp). No BLOCK-PENDING-FIX condition (no isolated defect; Catastrophic outcome IS the diagnostic signal).

### Anchor-frame audit verifies verdict robustness (Critic Phase 7.5)

| Frame | /020 BTC-only | BTC-in-pool baseline | Δ | Band |
|---|---|---|---|---|
| net_pnl trade-sum | −23.25% | +9.93% | −33.18 pp | NEGATIVE |
| **net_pnl monthly-sum** | −10.17% (OOS) | +33.17% | **−43.34 pp** | **Catastrophic** |
| **annualized-daily-Sharpe vs brief proxy +0.30** | −0.5566 | +0.30 | **−0.86** | **Catastrophic** |
| **annualized-daily-Sharpe vs reconstructed proxy +1.0** | −0.5566 | +1.00 | **−1.56** | **Catastrophic** |

3 of 4 frames land Catastrophic-NEGATIVE. Verdict cell ROBUST. Brief pre-registered Sharpe-Δ frame as decisive at Section 8 Row 6 — that pre-registration fires unambiguously.

## What Failed

### H_POOL_ANCHOR refutation at monthly aggregate was MISLEADING

Phase 2 EDA at `analysis/iteration_v1-020/btc_pool_anchor_summary.csv` computed monthly Pearson(BTC, ETH) net_pnl = **−0.0220** / Spearman **+0.0227** / same-sign rate **51.7%**. The EDA inferred: "Pool is essentially **independent training streams** across BTC↔ETH" and used this to refute H_POOL_ANCHOR.

**The inference was wrong**. Monthly aggregate Pearson does NOT capture training-time pool dependence. Three pool-conferred channels carry BTC's OOS positive rotation, NONE visible at monthly aggregate (LM Master Phase 7.4 §3 ADOPTED):

1. **Shared feature normalization at training time** — rolling 50-bar features compute per-symbol but Optuna trial selection on COMBINED IS labels picks splits favoring features whose value distribution is regular across all 5 cohorts. BTC-alone trains on BTC's narrower NATR distribution and Optuna lands in a different basin.
2. **Label-timing co-location** — training months containing BTC labels also contain ETH/LINK/LTC/DOT labels; Optuna's IS loss surface is integrated over all of them. Best-trial selection optimizes for JOINT loss; BTC-conditional optimum within that joint solution differs from BTC-alone optimum.
3. **Sample weighting (`abs_pnl`)** — BTC's large-magnitude trades are downweighted RELATIVE to LINK/LTC vol-amplified trades in the pool; BTC-only retraining REMOVES this implicit downweighting.

**This is the critical structural finding of /020.** QR's pool-anchor diagnostic at monthly granularity is a **methodological false-negative** for the training-time mechanism. The correct diagnostic substrate is training-time (Optuna best-trial parameter delta between pool and cohort-only at SAME seed), NOT monthly aggregate Pearson.

### LM Master Phase 4.5 directional track 0/3 calls

Three directional calls staked at Phase 4.5; all three REFUTED at Phase 7.4:

1. **INERT-no-effect modal at 40%** — REFUTED (NEGATIVE-CATASTROPHIC 2% tail materialized instead; modal off by 0.86σ in opposite direction)
2. **Jaccard prediction [0.10, 0.25] higher than /018+/019 ≈ 0.04** — REFUTED (observed 0.084 combined; OOS 0.048 BIT-IDENTICAL to /018+/019 alternative branch)
3. **BTC-only's /027 role as DIVERSIFICATION not ADDITIVE EDGE** — VINDICATED in direction but understated magnitude (actual NEGATIVE additive contribution, not diversification-neutral; /027 must EXCLUDE BTC-only, NOT just down-weight it)

LM Master Phase 4.5 §4 pre-registered the alternative-branch interpretation: "If observed Jaccard ≈ 0.04 (matching /018+/019): pool independence claim is at higher-than-monthly granularity — within-month label timing IS coupling BTC+ETH. Surprise outcome." That pre-registration is the only thing that prevented the LM Master post-mortem from being purely confessional. **Track record update: LM Master directional 0/3 on /020 + 1/1 methodology + 1/1 alternative-branch pre-registration utility.**

### Modal verdict cell INERT 60% REFUTED — tail materialized

QR POST-EDA prior (brief Section 5; LM Master Phase 4.5 §1 ADOPTED) sat at:
- PROMISING 20% / INERT 60% / NEGATIVE 20% (within NEGATIVE: 13% basin + 5% INTRINSIC + 2% CATASTROPHIC)

**Observed: NEGATIVE-CATASTROPHIC**. The 2% tail materialized. Modal INERT 60% REFUTED by tail outcome — 30× off the modal expectation; 9× off the negative-band combined; 1× exact match for the catastrophic-band subset.

Per LM Master Phase 7.4 §4 predictive failure analysis: each arrow in the prior chain `monthly ρ ≈ 0 → pool independent → Optuna basin proximity → trade roster overlap → small Sharpe Δ` was wrong. The structural finding is that monthly aggregate ρ ≈ 0 ≠ training-time pool independence.

### F-AXIS-MECHANISM #2 OOS BREACH-HIGH +7 vs LM Master tighter sub-band

LM Master Phase 4.5 §2 predicted OOS trade-count sub-band [25, 46] (mid 34) inside QR blocking band [25, 55]. Observed OOS 53 — outside LM sub-band by +7, inside QR band. **INFORMATIONAL per /019 framework — does NOT trigger F-AXIS #2 BREACH** (LM Master sub-bands sit INSIDE QR blocking band; only QR blocking band breaches trigger F-AXIS BREACH).

But it does reflect basin relocation: BTC-only Model H trades more (53) than pooled Model A on BTC (35). Combined with Jaccard 0.084 (only 4/35 OOS pool trades retained), the basin relocated AND took more trades AT WORSE Sharpe — a structurally adverse trade subset. This is the Phase 7.4 §4 Arrow 4 mechanism — small Jaccard need not produce small Sharpe Δ if the relocated basin samples a structurally adverse subset.

### Engineering report MISSING at Phase 7.5 dispatch (Critic Rec #1, 2nd cycle-3 incident)

Per Critic Phase 7.5 Recommendation #1: `briefs-v1/iteration_v1-020/engineering_report.md` was NOT emitted at Phase 6 closure. This is the **2nd cycle-3 incident** after /019. The skill-layer/orchestrator permanent fix from /017 closeout's 6th-strike protocol was supposed to address this; it didn't fire correctly at /019 OR /020.

**Phase 8 closeout addresses retrospectively** (engineering_report.md written from existing CSVs at Phase 8 closeout; zero backtest re-run). The retrospective engineering_report.md also RESOLVES Critic's F-AXIS #3 INDETERMINATE status (IS_H1 net_pnl = −21.95% inside band — confirmed BORDERLINE PASS).

Carry-forward action: re-confirm orchestrator Phase 6 contract addition requiring engineering_report.md in the same commit as comparison.csv (NOT QR scope this iteration). Two consecutive cycle-3 incidents means the permanent fix needs to be reconfirmed at the skill-layer.

## Path Forward (from Critic + LM Master CONVERGENT recommendation)

Verbatim from Critic Phase 7.5 review.md §"Path Forward" + LM Master Phase 7.4 §5:

1. **Methodology pivot to `_write_feature_importance` + training-time pool-anchor diagnostic** — family: **methodology-pivot** [Critic preference #1; LM Master Option C]. Add `feature_importance.csv` output (closing /019 §6 outstanding gap) AND per-(symbol, month) Optuna best-trial parameter delta between BTC-in-pool (Model A) and BTC-only (Model H) at SAME seed=42. Produces concrete training-time pool-anchor evidence. If diagnostic confirms LM Master §3 mechanism, /021 = LAST EXPLORATION before /027 CONFIRMATION moves up. ~25 min wall-clock.

2. **NEW feature family axis — funding-rate z-score or open-interest delta** — family: **feature-family**. Per /019 Critic Rec #3 carry-forward. Add single NEW feature (8h funding rate z-score, OR perp OI delta) to V1_FEATURE_COLUMNS_PRUNED. NOT touched in cycle-3 to date. Falsifier: importance rank ≥ 30% on ≥2 cohorts at IS.

3. **Risk-primitive axis — per-cohort drawdown brake** — family: **risk-primitive**. Binary off/on at -25% per-cohort cumulative loss. Tests whether risk gates dissolve OOS concentrated-loss pattern. Pre-commit deadlock-impossibility proof (A8 catalog + iter-v3/054 lesson): 8-candle cooldown escape.

Critic does NOT concur with strict adherence to LM Master Phase 4.5 §6 pre-staged /021 = LTC-only specialization. /020 catastrophic outcome materially shifts evidence base. QR should choose ONE of #1/#2/#3 (Critic preference: #1 > #2 > #3) with explicit Section 0.6 rotation justification.

**QR provisional adoption for /021**: Critic preference #1 (methodology pivot) — convergent with LM Master §5 hybrid Option C + B. /021 = methodology iteration on cheap budget:
- (i) Add `_write_feature_importance` per (model, symbol, train_month) emission to v1 runner per LM Master Phase 7.4 §6 (closes /019 §6 outstanding gap).
- (ii) Add training-time pool-anchor diagnostic — per-fold Optuna best-trial parameter delta between BTC-in-pool (Model A) and BTC-only (Model H) at SAME seed=42. Quantifies the 3 pool-conferred channels (feature normalization, label-timing co-location, abs_pnl weighting) at training-time granularity.
- (iii) Compute per-cohort Jaccard against pool baseline OFFLINE for LTC + DOT to PREDICT /022-/026 outcomes BEFORE spending wall-clock on full EXPLORATIONs.

**Verdict-conditional /022 staging**:
- If /021 diagnostic confirms LM Master §3 mechanism (LTC + DOT both have high pool-conferred edge signature): /022 = /027 CONFIRMATION moved up with 2-specialist bundle (LINK + ETH+gate) regressing against BTC-in-pool baseline (BTC IN POOL).
- If /021 diagnostic shows different pattern (LTC and/or DOT pool-INDEPENDENT): /022 = continue cohort coverage selectively with pool-independent cohort isolation.

## 6 LESSONS for v1 Cycle-3 Catalog

### LESSON #1: H_INTRINSIC REFUTED AT TRAINING-TIME GRANULARITY (monthly aggregate ρ ≈ 0 is misleading)

BTC IS/OOS trajectory across baseline + /014/015/016/017 + /020:

| Iter | BTC IS net_pnl_pct | BTC OOS net_pnl_pct |
|---|---|---|
| baseline | −37.28% | **+33.17%** |
| /014 | −24.25% | +5.70% |
| /015 | −0.65% | −7.18% |
| /016 | −34.60% | −8.31% |
| /017 | **−93.81%** | +15.11% |
| **/020 (BTC-only isolation)** | **−23.25%** | **+0.99%** (OOS Sharpe −0.5566 catastrophic) |

BTC's OOS positive rotation (+33.17% baseline) is **DISSOLVABLE under pure cohort isolation** (no gate, no specialization). Monthly aggregate ρ ≈ −0.022 between BTC and ETH PnL is a **methodological false-negative** for training-time pool dependence. Within-month label-timing carries BTC's edge.

**Codified rule**: future per-cohort EXPLORATIONs MUST NOT rely on monthly-aggregate pool-independence diagnostic as predictive evidence of isolation viability. Required diagnostic substrate is **training-time** (Optuna best-trial parameter delta between pool and cohort-only at SAME seed) OR an orthogonal mechanism (gate / feature / labeling) added on top of isolation.

### LESSON #2: PER-COHORT ISOLATION SUCCESS REQUIRES INDEPENDENT POSITIVE PRIOR OR ORTHOGONAL MECHANISM (NOT pool-anchor refutation per se)

Three-cohort comparison (LINK / ETH / BTC) establishes the principle:
- **LINK** (/018, structurally-positive prior): isolation PRESERVED OOS positive (+52.16 baseline → +53.80 /018); pool was NOT load-bearing for LINK.
- **ETH** (/019, structurally-negative prior + gate): isolation PLUS orthogonal mechanism (BTC-trend gate) DISSOLVED OOS negative (+2.75 baseline → +32.65 /019); the gate was the load-bearing mechanism.
- **BTC** (/020, asymmetric-rotation prior, NO knob): isolation ALONE LOST pool-conferred OOS positive (+33.17 baseline → +0.99 /020). The pool WAS load-bearing for BTC.

**Codified rule**: cohort isolation success requires either (a) independent positive prior at pool level (LINK case) OR (b) ORTHOGONAL mechanism added on top of isolation (ETH+gate case) — NOT pool-anchor-refutation per se. Future per-cohort EXPLORATIONs without methodology pivot or orthogonal mechanism are predicted to repeat the BTC pattern at single-seed EXPLORATION budget for cohorts with asymmetric or pool-conferred priors.

### LESSON #3: TRAINING-TIME POOL-ANCHOR DIAGNOSTIC IS THE LOAD-BEARING SUBSTRATE (NOT monthly aggregate)

The three training-time channels (per LM Master Phase 7.4 §3):
1. **Shared feature normalization at training time** (per-symbol rolling stats integrated into joint Optuna IS loss)
2. **Label-timing co-location** (joint IS loss surface across all 5 cohorts at each 8h candle)
3. **Sample weighting `abs_pnl`** (large-magnitude trades from one cohort downweighted by other cohorts' large-magnitude trades)

NONE of these are visible at monthly aggregate Pearson(BTC, ETH). Required diagnostic: per-fold Optuna best-trial parameter delta between pool and cohort-only at SAME seed.

**Codified rule**: /021 adds training-time pool-anchor diagnostic to v1 runner. Future per-cohort EXPLORATIONs Section 2 evidence MUST include training-time pool-anchor delta (NOT monthly aggregate Pearson alone). Cross-references: `feedback_v1_per_cohort_exploration_strategy` (refined; not refuted), `feedback_v1_h_intrinsic_refuted_at_btc` (THIS LESSON).

### LESSON #4: ENGINEERING REPORT TIMING CONTRACT — 2ND CYCLE-3 INCIDENT, PERMANENT FIX REQUIRED

Per Critic Phase 7.5 Recommendation #1: engineering_report.md missing at Phase 7.5 dispatch (2nd cycle-3 incident after /019). The skill-layer/orchestrator permanent fix from /017 6th-strike protocol was supposed to address this; it didn't fire correctly at /019 OR /020.

**Codified rule**: /021 brief Section 10.4 includes binding pre-commit "Phase 7.5 Critic will refuse to dispatch if engineering_report.md is missing" — the contract from /019 brief should be re-enforced at the orchestrator dispatch layer OR downgraded to "advisory" with documented justification. Two consecutive cycle-3 incidents = the contract needs re-confirmation at the skill-layer.

### LESSON #5: ANCHOR PROXY FORMALIZATION REQUIRED AT /027 (Critic Phase 7.5 Rec #2)

Brief Section 4 F1 uses a monthly Sharpe PROXY (+0.30) while comparison.csv reports annualized daily Sharpe. /018 and /019 implicitly used the same mixed-frame Δ rule. /020 anchor-frame audit confirmed the proxy holds across 4 frames (3 of 4 land Catastrophic) but the proxy itself is methodologically fragile.

**Codified rule**: /027 CONFIRMATION brief pre-computes BTC-in-pool annualized-daily-Sharpe directly (single deterministic number, no proxy) and locks the anchor frame to comparison.csv "sharpe" semantics. Forward-looking; /020 verdict ROBUST under all frames, but future iterations should not depend on proxy alignment.

### LESSON #6: /027 BUNDLE CONSTRAINED — 2 SPECIALISTS + BTC-IN-POOL (NOT 4-6 specialists; BTC-only EXCLUDED)

After /020, /027 bundle composition: **2/4-6 specialists viable** (LINK +0.80 + ETH+gate +0.50). BTC-only Model H EXCLUDED (NEGATIVE additive contribution per /020); BTC enters /027 IN POOL via Model A.

**Codified rule**: /027 CONFIRMATION brief design must (a) NOT include BTC-only Model H in bundle, (b) regress bundle against BTC-IN-POOL baseline (not BTC-only), (c) maintain cross-correlation < 0.40 between LINK and ETH+gate specialist Sharpe paths (Critic /019 Rec #3 pre-validation pre-registered). Future LTC and/or DOT specialists CONDITIONAL on /021 training-time diagnostic outcome — if LTC/DOT also have pool-conferred edge, they too are EXCLUDED from the bundle (enter /027 in pool).

## Cycle-3 Cadence Status (after /020)

- Cycle-3 EXPLORATION count: **5 of 10**
- CONFIRMATION earliest: **/027** (assuming sequential EXPLORATIONs from /021 to /026); **conditional /022** if /021 methodology diagnostic confirms LTC + DOT pool-conferred edge (LM Master §5 Option B)
- Edge ingredients merged this cycle: **0** (LINK-only specialist + ETH+gate specialist are CONDITIONAL carry-forwards to /027 substrate; /020 BTC-only EXCLUDED)
- Verdict distribution cycle-3 so far: 1 EXPLORATION-NEGATIVE catastrophic (/016) + 1 EXPLORATION-NEGATIVE anti-direction-INERT (/017) + 1 EXPLORATION-PROMISING favorable-INERT (/018) + 1 EXPLORATION-PROMISING (/019) + **1 EXPLORATION-NEGATIVE Catastrophic (/020)** = 2 PROMISING + 2 NEGATIVE clean + 1 NEGATIVE Catastrophic across 5 cycle-3 EXPLORATIONs
- BASELINE_V1.md unchanged at `v0.v1-baseline-corrected` (`f8bc12c`)
- **Methodology refined (NOT validated 2/2 anymore — 2/3 with caveat)**: per-cohort 2 of 3 PROMISING (LINK + ETH+gate succeed under different mechanisms); BTC isolation alone produces NEGATIVE Catastrophic. Per-cohort axis EFFECTIVELY SATURATED at pure isolation; future EXPLORATIONs require methodology pivot or orthogonal mechanism

## Track Record Update

- **Verdict-class directional track**: 3/17 → **3/18** (no new directional hit; modal INERT 60% prior REFUTED with 2% tail materialized)
- **Mechanism-level track**: 9/17 → **9/18** (no new mechanism-level hit; F-AXIS-MECHANISM #3 BORDERLINE PASS via retrospective engineering_report.md does not count as Phase 4.5 prediction confirmation)
- **LM Master directional track**: 3/17 → **3/20** (Phase 4.5 0/3 calls + 1/1 methodology n_eff=9 PASS + 1/1 alternative-branch pre-registration utility)
- **LM Master mechanism-level track**: 9/17 → **9/20** (n_eff PASS exact + alternative-branch pre-registration utility account for partial credit)

LM Master Phase 4.5 prediction record on /020:

| Phase 4.5 prediction | Observed | Hit/Miss |
|---|---|---|
| INERT-no-effect modal 40% / INERT-preserved 20% / PROMISING 20% / NEGATIVE-basin 13% / NEGATIVE-INTRINSIC 5% / **CATASTROPHIC 2%** | **NEGATIVE-CATASTROPHIC** (OOS Δ -0.86) | **REFUTED** (2% tail materialized; modal off 0.86σ opposite) |
| F-AXIS #2 IS trades predicted [79, 147] mid 105 | observed **122** | **HIT** (LM band PASS, inside QR + LM) |
| F-AXIS #2 OOS trades predicted [25, 46] mid 34 | observed **53** | **MISS HIGH +7** (LM BREACH-HIGH, inside QR — INFORMATIONAL) |
| n_eff_per_cell [7, 10] point 9 | observed **9** | **HIT EXACT** |
| OOS Sharpe Δ band predicted [0, +0.10] modal | observed **-0.86** | **REFUTED** (2% tail outcome) |
| Jaccard IS+OOS combined predicted [0.10, 0.25] higher than /018+/019 | observed **0.084** (IS 0.098 / OOS 0.048) | **REFUTED**; matches /018+/019 alternative branch |
| §4 alternative-branch pre-registered: Jaccard ≈ 0.04 → pool independence at higher-than-monthly granularity | OBSERVED | **HIT** (alternative-branch pre-registration utility) |

Net: **1/7 HIT EXACT (n_eff), 1/7 HIT (IS trade-count), 1/7 MISS HIGH +7 (OOS trade-count, informational), 3/7 REFUTED (modal, OOS Sharpe Δ, Jaccard), 1/7 HIT alternative-branch pre-registration**. Phase 4.5's directional calls (INERT modal + Jaccard high) refuted; methodology calls (n_eff) and alternative-branch pre-registration utility vindicated.

## Phase 4.5 LM Master Prediction Calibration (Section 13 brief self-check)

Phase 4.5 LM Master prior: PROMISING 25% / INERT 50% / NEGATIVE 25%. After EDA: PROMISING 20% / **INERT 60%** (40% no-effect + 20% preserved-asymmetric) / NEGATIVE 20% (13% basin + 5% INTRINSIC + **2% CATASTROPHIC**).

**Observed: NEGATIVE-CATASTROPHIC**. The 2% tail materialized — modal INERT 60% REFUTED by 30× factor on modal-band match.

**Calibration takeaway**: at single-cohort EXPLORATIONs with asymmetric IS/OOS priors and NO knob, the modal INERT prior assumes pool independence — which is a methodological false-negative if monthly aggregate ρ is used as the substrate. The LM Master Phase 4.5 §4 alternative-branch pre-registration is the only thing that prevented post-mortem confessional mode. Future LM Master advisories on per-cohort EXPLORATIONs should weight tail outcomes higher when the cohort prior is asymmetric AND the cohort isolation has no orthogonal mechanism.

## /027 Bundle Composition Update

Per LM Master Phase 7.4 §5 + Critic Phase 7.5 Path Forward + /019 closeout LESSON #4 (regression target methodology):

| Specialist | Status after /020 | Single-seed Δ | /027 multi-seed regression target |
|---|---|---|---|
| **LINK-only /018** | VALIDATED — LOAD-BEARING | +0.16 | **+0.80** |
| **ETH-only + BTC-trend gate /019** | VALIDATED — LOAD-BEARING | +0.65 | **+0.50** |
| **BTC-only /020** | **NEGATIVE Catastrophic — EXCLUDED from /027** | **−0.86** | **EXCLUDED** |
| LTC-only /021+ | PENDING (depends on /021 methodology diagnostic outcome) | — | — |
| DOT-only /022+ | PENDING | — | — |
| Pooled cohorts /023-/026 | PENDING | — | — |

**Current /027 bundle composition**: **2/4-6 specialists viable** (LINK + ETH+gate); BTC-only EXCLUDED; BTC enters /027 IN POOL via Model A (no architectural change vs baseline for BTC). Projected portfolio Sharpe lift +0.85 to +1.05 with 2 specialists + BTC-IN-POOL pooled anchor; cross-correlation < 0.40 between LINK and ETH+gate roster Sharpe paths still required (Critic /019 Rec #3 pre-validation).

## Path Forward (from Critic)

Verbatim from `briefs-v1/iteration_v1-020/review.md` §"Path Forward":

> Critic CONCURS with LM Master Phase 7.4 §5 hybrid Option C+B and adds structural alternatives.
>
> 1. **Methodology pivot to `_write_feature_importance` + training-time pool-anchor diagnostic** — family: **methodology-pivot** [Critic preference #1]. Add `feature_importance.csv` output (closing /019 §6 outstanding gap) AND per-(symbol, month) Optuna best-trial parameter delta between BTC-in-pool (Model A) and BTC-only (Model H) at SAME seed=42. Produces concrete training-time pool-anchor evidence. If diagnostic confirms LM Master §3 mechanism, /021 = LAST EXPLORATION before /027 CONFIRMATION moves up. ~25 min wall-clock.
>
> 2. **NEW feature family axis — funding-rate z-score or open-interest delta** — family: **feature-family**. Per /019 Critic Rec #3 carry-forward. Add single NEW feature (8h funding rate z-score, OR perp OI delta) to V1_FEATURE_COLUMNS_PRUNED. NOT touched in cycle-3 to date. Falsifier: importance rank ≥ 30% on ≥2 cohorts at IS.
>
> 3. **Risk-primitive axis — per-cohort drawdown brake** — family: **risk-primitive**. Binary off/on at -25% per-cohort cumulative loss. Tests whether risk gates dissolve OOS concentrated-loss pattern. Pre-commit deadlock-impossibility proof (A8 catalog + iter-v3/054 lesson): 8-candle cooldown escape.
>
> Critic does NOT concur with strict adherence to LM Master Phase 4.5 §6 pre-staged /021 = LTC-only specialization. /020 catastrophic outcome materially shifts evidence base. QR should choose ONE of #1/#2/#3 (Critic preference: #1 > #2 > #3) with explicit Section 0.6 rotation justification.

## Axis Rotation Status (v1-only)

- **This iter's family**: `per-cohort-specialization-BTC` (NEW 11th family — FIRST usage at v1 catalog level; THIRD per-cohort EXPLORATION at v1 catalog level under USER STRATEGIC PIVOT after LINK /018 + ETH+gate /019)
- **Prior 5 EXPLORATION families** (going INTO /020): labeling CONFIRMATION (/015), sample-weighting (/016), universe (/017), per-cohort-specialization-LINK (/018), per-cohort-specialization-ETH (/019)
- **Rotation honored**: YES — `per-cohort-specialization-BTC` is in NONE of the prior 5 families. Per /018 + /019 closeout LESSONs (codified rule), per-cohort specialization is the cycle-3 methodology; BTC is a different COHORT from LINK and ETH (rotation by cohort, not by family literal-name). 3-way Critic + LM Master + QR orthogonality convergence on cohort-pairing differentiation.
- **Updated prior 5 going into /021**: sample-weighting (/016), universe (/017), per-cohort-specialization-LINK (/018), per-cohort-specialization-ETH (/019), per-cohort-specialization-BTC (/020)
- **/021 axis-family (per Critic + LM Master CONVERGENT recommendation)**: `methodology-pivot` (REUSE 6th catalog family `methodology` — methodology refinement to add `_write_feature_importance` + training-time pool-anchor diagnostic; supersedes LM Master Phase 4.5 §6 pre-staged LTC-only specialization in light of /020 evidence shift)

## Next Iteration Ideas (cycle-3 sixth EXPLORATION = /021)

Per Critic + LM Master CONVERGENT Path Forward + /020 mechanism-level structural finding:

1. **/021 = methodology pivot (PRIMARY per Critic Path Forward #1 + LM Master §5 hybrid Option C + B)** — family `methodology-pivot` (REUSE 6th catalog family `methodology` from /001). Add `_write_feature_importance` per (model, symbol, train_month) emission to v1 runner (closes /019 §6 outstanding gap) AND add training-time pool-anchor diagnostic — per-fold Optuna best-trial parameter delta between BTC-in-pool (Model A) and BTC-only (Model H) at SAME seed=42. ~25 min wall-clock. Produces concrete training-time pool-anchor evidence to predict LTC + DOT outcomes before wall-clock spend.

2. **/022+ verdict-conditional staging**:
   - If /021 diagnostic confirms LM Master §3 mechanism (LTC + DOT both have high pool-conferred edge signature): /022 = /027 CONFIRMATION moved up with 2-specialist bundle (LINK + ETH+gate) regressing against BTC-in-pool baseline (BTC IN POOL).
   - If /021 diagnostic shows different pattern (LTC and/or DOT pool-INDEPENDENT): /022 = continue cohort coverage selectively with pool-independent cohort isolation. LTC-only (worst OOS contributor baseline -47.25%) or DOT-only (IS +96.07 at /017 catastrophic-positive rotation).

3. **/021 axis-FAMILY alternative options** (carried for future use):
   - **NEW feature family — funding-rate z-score** (Critic Path Forward #2) — Add single NEW feature to V1_FEATURE_COLUMNS_PRUNED. NOT touched in cycle-3 to date. Falsifier: importance rank ≥ 30% on ≥2 cohorts at IS.
   - **Risk-primitive — per-cohort drawdown brake** (Critic Path Forward #3) — Binary off/on at -25% per-cohort cumulative loss. Pre-commit deadlock-impossibility proof per A8 catalog + iter-v3/054 lesson.

All cycle-3 sixth EXPLORATION (/021) QR EDA-justifies methodology pivot under 2h wall-clock cap.

## Files & Commits on Branch

- Branch: `iteration-v1/020` from `iter-v1/019` closeout (tag `v0.v1-019`)
- HEAD at QR Phase 1-4 + LM Master Phase 4.5: `9c6c32f`
- HEAD at brief Phase 5 + EDA: `377c6af`
- HEAD at Section 3.4 LM Master responses + final brief: `88982dc`
- HEAD at Phase 5.5 gate PASS: `056c649`
- HEAD at QE implementation + dispatch: `cc243f5`
- HEAD at Critic Phase 6.0 PASS: `c810317`
- HEAD at LM Master Phase 7.4 post-mortem: `1d6a25b`
- HEAD at Critic Phase 7.5 review (EXPLORATION-NEGATIVE Catastrophic): `ebdc4a6`
- HEAD at engineering report (retrospective at Phase 8 per Critic Rec #1): `bbf588a`
- HEAD at Phase 7 evaluation memo: `bd464a1`
- HEAD at Phase 8 closeout (THIS COMMIT): TBD
- Reports artifacts in `reports-v1/iteration_v1-020/`

Key commits in /020:
- `283064b` — feat: EDA — BTC IS catastrophic rotation hypothesis tests
- `377c6af` — docs: QR Phases 1-5 + per-cohort-specialization-BTC brief
- `8e6f3c4` — docs: Phase 4.5 LM Master advisory
- `88982dc` — docs: Section 3.4 LM Master responses + INERT subtype refinement
- `056c649` — docs: phase 5.5 gate PASS
- `cc243f5` — feat: BTC-only specialization (Model H single-cohort)
- `c810317` — docs: Phase 6.0 Critic pre-flight PASS
- (Backtest dispatched; comparison.csv + reports artifacts in `reports-v1/iteration_v1-020/`)
- `1d6a25b` — docs: Phase 7.4 LM Master post-mortem — NEGATIVE-CATASTROPHIC
- `ebdc4a6` — docs: Phase 7.5 Critic review — EXPLORATION-NEGATIVE Catastrophic
- `bbf588a` — docs: engineering report (RETROSPECTIVE per Critic Rec #1)
- `bd464a1` — docs: Phase 7 OOS evaluation memo
- (Phase 8 closeout this commit) — Phase 8 diary + merge decision (NO-MERGE)

**Trunk merge**: NONE. EXPLORATION-NEGATIVE Catastrophic does NOT update BASELINE_V1.md (per `feedback_v3_baseline_update_policy.md` adopted by v1 — only CONFIRMATION-MERGE updates baseline). BTC-only Model H specialist EXCLUDED from /027 substrate; BTC enters /027 IN POOL via Model A (no architectural change vs baseline for BTC). NO src/ trunk merge from this iteration.

**Tag**: `v0.v1-020` to be applied after this Phase 8 closeout commit.
