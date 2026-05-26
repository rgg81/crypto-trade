# iter-v1/020 — Phase 7 OOS Evaluation Memo

**Iteration**: iter-v1/020 (cycle-3 EXPLORATION #5 of 10; THIRD per-cohort EXPLORATION; BTC IS-NEG/OOS-POS asymmetric-rotation cohort)
**Phase**: 7 — Evaluation (FIRST time OOS data is interpreted; pre-Phase-8 closeout)
**Branch**: `iteration-v1/020` from `iter-v1/019` closeout
**HEAD**: `ebdc4a6`
**Reports**: `reports-v1/iteration_v1-020/{in_sample,out_of_sample}/`
**Engineering report (retrospective)**: `reports-v1/iteration_v1-020/engineering_report.md`
**Critic verdict (Phase 7.5)**: EXPLORATION-NEGATIVE Catastrophic-NEGATIVE (Section 8 Row 6)
**LM Master Phase 7.4**: H_INTRINSIC REFUTED — pool-conferred OOS positive rotation via 3 training-time channels

---

## 1. F1 / F3 Actual vs Predicted

### F1 OOS Sharpe Δ vs BTC-in-pool anchor

- **Pre-registered band (brief Section 4 F1)**: PROMISING ≥ +0.20; INERT ∈ [−0.20, +0.20]; NEGATIVE ≤ −0.20; **Catastrophic ≤ −0.55**.
- **Anchor (brief Section 4)**: BTC-in-pool OOS Sharpe proxy ≈ **+0.30** (monthly Sharpe; reconstructed from baseline `analysis/iteration_v1-020/btc_regime_concentration.csv`).
- **Observed**: BTC-only OOS Sharpe = **−0.5566** (annualized daily from comparison.csv).
- **Δ**: −0.5566 − 0.30 = **−0.8566 → Catastrophic-NEGATIVE band**.
- **Status**: Section 8 Row 6 FIRES decisively (F1 OOS Δ ≤ −0.55 → NEGATIVE-CATASTROPHIC; band-violation OK on F-AXIS #2/#3).

### F3 IS Sharpe Δ vs BTC-in-pool IS anchor

- **Pre-registered band (brief Section 4 F3)**: PROMISING ≥ +0.20; INERT ∈ [−0.20, +0.20]; NEGATIVE ≤ −0.20; Catastrophic-NEGATIVE ≤ −0.30.
- **Anchor (brief Section 4)**: BTC-in-pool IS Sharpe proxy ≈ **−0.12** monthly.
- **Observed**: BTC-only IS Sharpe = **−0.5914** (annualized daily).
- **Δ**: −0.5914 − (−0.12) = **−0.4714 → Catastrophic-NEGATIVE F3 band**.
- **Status**: F3 reinforces F1 — IS catastrophic was PRESERVED (regime-bound finding partially holds at F-AXIS #3 = BORDERLINE PASS, −21.95% vs band [−45%, −15%]) but IS Sharpe Δ collapsed beyond the F3 Catastrophic threshold.

### Verdict-cell interpretation

**Predicted modal (LM Master Phase 4.5 + brief Section 5)**: INERT 60% — modal cell INERT-no-effect (|Δ|<0.10). Tail outcomes: PROMISING 20%, NEGATIVE-basin 13%, NEGATIVE-INTRINSIC 5%, NEGATIVE-CATASTROPHIC 2%.

**Observed**: NEGATIVE-CATASTROPHIC — **2% tail materialized**; modal INERT 60% **REFUTED** by 0.86σ in the OPPOSITE direction from the modal expectation.

**Resolution**: Section 8 Row 6 (F1 Δ ≤ −0.55) is the binding falsifier. Modal cell REFUTED by tail outcome — the LM Master Phase 4.5 §1 prior chain (monthly ρ ≈ 0 → pool independent → basin proximity → small Δ) was wrong at every step (per LM Master Phase 7.4 §4 predictive failure analysis).

## 2. F-AXIS-MECHANISM Actual vs Predicted

| Sub-check | Pre-registered band | Observed | Status | Interpretation |
|---|---|---|---|---|
| **#1 Dispatch correctness** | per_symbol.csv 100% BTCUSDT IS+OOS | 100% BTCUSDT both halves; trades.csv 175 BTC rows / 0 other | **PASS** | Model H exclusive dispatch via `V1_ITER020_UNIVERSE` guard worked cleanly. |
| **#2 Trade-count band (LOAD-BEARING per /019 Critic Rec #2)** | QR: IS ∈ [70, 150]; OOS ∈ [25, 55]. LM tighter sub-band: IS ∈ [79, 147]; OOS ∈ [25, 46]. | IS **122** ∈ both bands; OOS **53** ∈ QR band, **outside LM sub-band by +7** | **PASS (QR blocking band); LM Master BREACH-HIGH +7 INFORMATIONAL** | LM Master Phase 4.5 §2 sub-bands sit INSIDE the QR blocking band — values outside LM sub-band but inside QR blocking band do NOT trigger F-AXIS #2 BREACH. OOS over-trades by ~7 vs LM tighter mid; reflects basin-relocation taking the BTC-only model into a different trade-rate region than pooled Model A. INFORMATIONAL — does not affect verdict. |
| **#3 IS_H1 catastrophic preservation (regime-binding test)** | IS_H1 ∈ [−45%, −15%] PASS; IS_H1 ≥ −10% DISSOLVED; IS_H1 ≤ −60% AMPLIFIED | IS_H1 = **−21.95%** (computed in engineering_report.md §3) inside band near upper boundary −15% | **BORDERLINE PASS (resolved here from Critic INDETERMINATE)** | Critic estimated −19.4% pending engineering_report.md. Computed: −21.95% — inside band but near upper boundary. Regime-bound IS catastrophic CHARACTER preserved; absolute magnitude REDUCED from baseline IS_H1 = −36.01% (Δ +14.06pp). The IS regime constraint is partial — BTC-only Optuna trajectory at narrower scope DID escape ~14pp of baseline IS_H1 catastrophic, but the OOS positive rotation collapsed simultaneously (the dominant effect on verdict). |
| **#4 n_eff_per_cell band (informational)** | LM Master predicted [7, 10] point estimate **9** | observed **9** | **PASS (matches LM Master point estimate exactly)** | n_eff methodology calibration accurate per /019 §5 update (n_eff predicted from training row count, not post-hoc kept trades). Matches /018 LINK-only (9). |

**Compound F-AXIS verdict**: PASS on mechanism (#1 + #3 + #4 PASS; #2 PASS at QR blocking band). Catastrophic-NEGATIVE verdict at F1 fires DESPITE F-AXIS PASS — the F-AXIS mechanism checks confirmed dispatch correctness and partial IS regime preservation, but **OOS Sharpe Δ at −0.86 is the load-bearing falsifier** (Section 8 Row 6: "(band-violation OK)" on F-AXIS).

The structural reading: F-AXIS preservation + F1 catastrophic = **the IS regime profile was preserved but the OOS positive rotation was LOST**. This pattern would not be diagnosable from monthly aggregate ρ ≈ 0 — it requires the Jaccard analysis at Phase 7.4 (0.084 combined → basin relocation into structurally adverse OOS subset) plus LM Master §3 mechanism analysis.

## 3. EDA Prediction Calibration

### H_POOL_ANCHOR diagnostic was MISLEADING at monthly aggregate

Phase 2 EDA (`analysis/iteration_v1-020/btc_pool_anchor_summary.csv`) computed monthly Pearson(BTC, ETH) net_pnl = −0.0220 / Spearman +0.0227 / same-sign rate 51.7%. The EDA inferred: pool independent → modal INERT (no effect from cohort isolation).

**This inference was wrong**. Monthly aggregate Pearson does NOT capture training-time pool dependence. Three pool-conferred channels carry BTC's OOS positive rotation, NONE visible at monthly aggregate (LM Master Phase 7.4 §3):

1. **Shared feature normalization at training time** — rolling 50-bar features compute per-symbol but Optuna trial selection on COMBINED IS labels picks splits favoring features whose value distribution is regular across all 5 cohorts. BTC-alone trains on BTC's narrower NATR distribution and Optuna lands in a different basin.
2. **Label-timing co-location** — training months containing BTC labels also contain ETH/LINK/LTC/DOT labels; Optuna's IS loss surface is integrated over all of them. Best-trial selection optimizes for JOINT loss; BTC-conditional optimum within that joint solution differs from BTC-alone optimum.
3. **Sample weighting (`abs_pnl`)** — BTC's large-magnitude trades are downweighted RELATIVE to LINK/LTC vol-amplified trades in the pool; BTC-only retraining REMOVES this implicit downweighting.

### Corrected mental model (LM Master Phase 7.4 §3 ADOPTED)

Cohort isolation success requires:
- (a) **Independent positive prior at pool level** (LINK case — /018, both IS and OOS positive in pool; isolation PRESERVES), OR
- (b) **ORTHOGONAL mechanism added** on top of isolation (ETH+counter-trend-gate case — /019; the gate is the load-bearing mechanism, NOT isolation).

Pool-anchor refutation at monthly aggregate is **NEITHER sufficient NOR necessary** for isolation viability. The QR Section 0.4 EDA framing was a methodological false-negative.

### Predictive failure analysis (LM Master Phase 7.4 §4 ADOPTED)

The Phase 4.5 §1 modal INERT-no-effect prior chain:

`monthly ρ ≈ 0 → pool independent → Optuna basin proximity → trade roster overlap → small Sharpe Δ`

Each arrow is wrong:
- **Arrow 1**: monthly ρ ≈ 0 does NOT imply training-time independence (§3 mechanisms).
- **Arrow 2**: even if pool were independent, single-cohort retraining at single-seed has wide basin-lottery variance for cohorts with asymmetric IS/OOS priors.
- **Arrow 3**: Jaccard 0.084 confirms basin moved substantially (5%-overlap region).
- **Arrow 4**: small Jaccard need not produce small Sharpe Δ if the relocated basin samples a structurally adverse trade subset (this is what happened).

### Calibration update for /021+ cohort-isolation reasoning

Audit at TRAINING-TIME granularity, not monthly aggregate:
1. Cohort's relative pool weight (BTC labels at ~24% of pool month-rows).
2. Cohort's label-timing co-location with other cohorts (8h candles: same `open_time` across symbols → labels are joint).
3. Cohort's label-noise dependence on cross-symbol sample weighting (abs_pnl integrates magnitudes across cohorts).
4. **Trained-IS-NEG / trained-OOS-POS asymmetry is a POOL-DEPENDENT artifact**, NOT an intrinsic property. Future cohorts with asymmetric priors (LTC, DOT) should be expected to LOSE the pool-conferred direction at single-cohort isolation.

## 4. Verdict-Class Priors — Modal MISSED; Tail Materialized

### Pre-registered prior (Phase 4.5 LM Master adopted into brief Section 5)

| Cell | Pre-registered probability | Subtype split |
|---|---|---|
| **PROMISING (Δ ≥ +0.20)** | 20% | basin reorganization at single-cohort labels |
| **INERT (Δ ∈ [−0.20, +0.20])** | **60% MODAL** | INERT-no-effect 40% + INERT-preserved-asymmetric 20% |
| **NEGATIVE (Δ ≤ −0.20)** | 20% | NEGATIVE-basin 13% + NEGATIVE-INTRINSIC 5% + **NEGATIVE-CATASTROPHIC 2%** |

### Observed verdict

**NEGATIVE-CATASTROPHIC (Section 8 Row 6)**. F1 OOS Δ = −0.86 ≤ −0.55 threshold. The **2% tail materialized**; modal INERT 60% **REFUTED**.

### Calibration update — LM Master Phase 4.5 directional track 0/3 calls

Phase 4.5 staked three directional calls:
1. **INERT-no-effect modal at 40%** — REFUTED (2% tail materialized instead)
2. **Jaccard prediction [0.10, 0.25] higher than /018+/019 ≈ 0.04** — REFUTED (observed 0.084 combined; OOS 0.048 matches /018+/019 alternative branch)
3. **BTC-only's /027 role as DIVERSIFICATION not ADDITIVE EDGE** — VINDICATED in direction but understated magnitude (actual NEGATIVE additive, not diversification-neutral)

Net: **0/3 directional Phase 4.5 calls** (this iteration); 1/1 methodology call vindicated (n_eff = 9 PASS); 1/1 alternative-branch pre-registration utility (§4 Jaccard ≈ 0.04 alternative branch was the realized branch — only because LM Master pre-registered it).

LM Master cumulative track (post-/020): **2/16 → 2/19 directional** (was 3/17 at /019; now 0/3 at /020 added). Mechanism-level: 9/17 → 9/20.

QR verdict-class directional track (post-/020): /015 C1-inversion 3/3 + /018 PROMISING-INERT favorable-confirmed-from-modal + /019 PROMISING from modal-adjacent + /020 NEGATIVE-CATASTROPHIC from 2% tail = **2 of 16 directional hits + 1 of 4 cycle-3 EXPLORATIONs ended in tail outcome**. Cycle-3 modal cell tracking is suspect for cohort-isolation axis — the QR + LM Master 60% modal INERT prior was off by a factor of 30× (modal observed at 1/4 across cycle-3; LM Master+QR predicted 6/10).

## 5. /027 CONFIRMATION Readiness

### Bundle composition after /020

| Specialist | Status after /020 | Single-seed Δ | /027 multi-seed regression target |
|---|---|---|---|
| **LINK-only /018** | VALIDATED — LOAD-BEARING | +0.16 | **+0.80** |
| **ETH-only + BTC-trend gate /019** | VALIDATED — LOAD-BEARING | +0.65 | **+0.50** |
| **BTC-only /020** | **NEGATIVE Catastrophic — CLOSED for isolation-without-gate** | **−0.86** | **EXCLUDED** |
| LTC-only /021+ | PENDING (depends on /021 methodology diagnostic outcome) | — | — |
| DOT-only /022+ | PENDING | — | — |
| Pooled cohorts /023-/026 | PENDING | — | — |

### Current readiness: 2 of 4-6 specialists confirmed

- **LINK-only +0.80 anchor** (validated /018)
- **ETH+gate +0.50 anchor** (validated /019)
- **BTC enters /027 via POOL (Model A)** — NOT via BTC-only Model H

Projected portfolio Sharpe lift with 2 specialists + BTC-IN-POOL anchor: **+0.85 to +1.05** (assumes cross-correlation < 0.40 between LINK and ETH+gate roster Sharpe paths; Critic /019 Rec #3 pre-validation required at /027 brief design).

### Bundle math implication

Original Section 0.2 of brief framed /020 as the **third structurally-distinct cohort** for /027 bundle. /020 NEGATIVE removes BTC-only as a viable additive specialist — bundle math now constrained to LINK + ETH+gate + BTC-IN-POOL pooled.

**Two strategic paths forward**:
1. **/027 CONFIRMATION moved up at /022 with 2-specialist bundle (LINK + ETH+gate) regressing against BTC-in-pool baseline** — LM Master Phase 7.4 §5 Option B; cancels /021-/026 cohort coverage.
2. **Continue cohort coverage /021-/026 selectively** — pursue LTC and/or DOT to find a 3rd or 4th specialist, with the constraint that future per-cohort isolation EXPLORATIONs require methodology pivot + orthogonal mechanism per LM Master §3 corrected mental model.

LM Master Phase 7.4 §5 RECOMMENDATION: **hybrid Option C + B**. /021 = methodology pivot (Option C — add `_write_feature_importance` + training-time pool-anchor diagnostic on a cheap budget). If /021 diagnostic shows LTC + DOT also lose pool-anchor at training time, proceed directly to /022 = /027 CONFIRMATION (Option B) with 2-specialist bundle, BTC IN POOL. Methodology investment up-front saves 4-5 wasted EXPLORATIONs.

Critic Phase 7.5 CONCURS with LM Master §5 hybrid Option C + B.

## 6. Honest Assessment — Per-Cohort Axis SATURATED Without Methodology Pivot

The cycle-3 per-cohort EXPLORATION ledger after /020:

| Iter | Cohort | Prior | Specialization | Verdict |
|---|---|---|---|---|
| /018 | LINK | positive (9/9 IS+OOS) | NONE (pure isolation) | PROMISING-INERT favorable |
| /019 | ETH | negative (5/5 OOS through cycle-3) | direction-aware BTC-trend gate | PROMISING |
| /020 | BTC | asymmetric (5/5 IS-NEG / 4/5 OOS-POS) | NONE (pure isolation, no knob) | NEGATIVE Catastrophic |

The pattern emerging:
- LINK isolation worked because pool was NOT load-bearing for LINK's positive prior.
- ETH isolation worked because the BTC-trend gate dissolved ETH's drag via an ORTHOGONAL mechanism, not isolation per se.
- BTC isolation FAILED because the pool WAS load-bearing for BTC's OOS positive rotation, and pure isolation removed it.

**Forward-looking inference**: per-cohort isolation EXPLORATIONs without methodology pivot or orthogonal mechanism are predicted to repeat the BTC pattern at single-seed EXPLORATION budget for cohorts with asymmetric or negative priors. The remaining 3-cohort axis (LTC, DOT, 2-sym pools) has:
- **LTC** (worst OOS contributor in baseline at −47.25%): high probability of repeating the BTC catastrophic pattern at pure isolation
- **DOT** (IS +96.07 at /017 catastrophic-positive rotation; IS +26.62 at baseline): asymmetric prior similar to BTC — high probability of repeating the BTC catastrophic pattern at pure isolation
- **2-sym pools (BTC+ETH or LINK+SOL)**: more axis options, but each requires a new orthogonality justification

**Honest assessment**: the per-cohort axis is **effectively SATURATED at single-cohort isolation without methodology pivot or orthogonal mechanism added on top of isolation**. The two PROMISING EXPLORATIONs (/018, /019) succeeded for case-specific reasons (LINK had independent positive prior; ETH succeeded due to the orthogonal gate). The catalog-level signal from /020 is: **pure cohort isolation as a single-axis EXPLORATION does not generalize to cohorts with pool-conferred edge — and most v1 cohorts have at least partial pool-conferred edge**.

This is not the kill switch for cycle-3 — it is a methodology refinement directive. /021 MUST address this. The Critic + LM Master CONVERGENT recommendation (methodology pivot — `_write_feature_importance` + training-time pool-anchor diagnostic) is the right next step. After /021 produces the training-time diagnostic, /022+ becomes either (a) /027 CONFIRMATION moved up if LTC/DOT show similar pool-anchor signature OR (b) selectively continued cohort coverage with orthogonal mechanism added per cohort.

## 7. Conclusion — Phase 7 Outputs Summary

- **Verdict**: EXPLORATION-NEGATIVE Catastrophic-NEGATIVE (Section 8 Row 6).
- **Key falsifier**: F1 OOS Sharpe Δ = −0.86 ≤ −0.55 threshold. Robust across all 4 anchor frames per Critic Phase 7.5 anchor-frame audit.
- **F-AXIS status**: #1 PASS, #2 PASS (QR blocking band; LM tighter sub-band BREACH-HIGH +7 INFORMATIONAL), #3 BORDERLINE PASS (IS_H1 = −21.95% inside band; resolved from Critic INDETERMINATE via §3 of engineering_report.md), #4 PASS exact.
- **Mechanism (load-bearing)**: H_INTRINSIC REFUTED at training-time granularity. BTC's OOS positive rotation was POOL-CONFERRED via 3 channels (shared feature normalization, label-timing co-location, abs_pnl sample weighting). Monthly aggregate ρ ≈ −0.022 was a methodological false-negative.
- **EDA calibration**: H_POOL_ANCHOR refutation at monthly aggregate was MISLEADING. Future per-cohort EXPLORATIONs require training-time diagnostic.
- **/027 readiness**: 2/4-6 specialists confirmed (LINK + ETH+gate). BTC enters /027 IN POOL via Model A. Bundle math constrained.
- **/021 axis**: methodology pivot per Critic + LM Master convergent hybrid Option C + B (add `_write_feature_importance` + training-time pool-anchor diagnostic).
- **Process recommendations to feedback rules**: engineering report timing contract (Critic Rec #1); anchor proxy formalization (Critic Rec #2); LM Master §3 structural finding adoption (Critic Rec #3).

Phase 7 evaluation complete. Phase 8 diary + merge decision (NO-MERGE) follows.
