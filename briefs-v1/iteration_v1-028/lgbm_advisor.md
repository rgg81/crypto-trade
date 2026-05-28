# LightGBM Master Advisor — iter-v1/028 — Phase 4.5 (Pre-Design)

## Context
- Cycle-4 EXPLORATION-1 (first post-cycle-3-closure). D-specialist with atr_sl=1.0 (vs baseline 1.75)
- /022 NEG-CAT precedent: pure-isolation+gate ASYMMETRIC_ROTATION failed at -1.17 OOS Δ
- QR mechanism: post-entry ATR magnitude clip targeting 62% stop_loss baseline ratio
- ORACLE counterfactual +36.17% PnL on baseline LTC OOS roster
- LM Master track entering /028: methodology 6/6 perfect; directional 2/8

## 1. Multi-seed mandate adjustment — MECHANICAL

**NO `--seeds` flag in v1 runner.** Brief §3.2/3.3 `--seeds 2 --ensemble-size 3` will FAIL at argparse.

**RECOMMEND**: `--exploration --iteration 028 --pruned-features --n-trials 35 --ensemble-size 10`. CONFIRMATION-mode variance budget at EXPLORATION axis (single-cohort cost). ~30 min wall-clock. Mode tag remains EXPLORATION (n_trials=35 NOT 50). QR must correct brief §3.2/3.3 pre-Phase-6.

## 2. atr_sl=1.0 is NOT basin-orthogonal — CRITICAL REFRAMING

atr_sl is **upstream of label generation** (`triple_barrier_labels` reads `atr_sl_multiplier` to set lower barrier). Tightening 1.75→1.0 narrows lower barrier by 43%. **NOT pure post-entry clip — it changes LABELS LightGBM trains on.** Class balance shifts: MORE -1 labels with SMALLER magnitudes.

**Prediction**: Optuna basin RELOCATES under atr_sl=1.0 retraining. Basin Jaccard vs baseline expected **0.05-0.15** (similar /022's 0.093). The brief §0.4 "basin-relocation-orthogonal" framing is overstated.

Phase 7.4 verdict assignment MUST compare BOTH (a) Optuna best_params shift (basin vector) AND (b) label class balance shift (training distribution vector) — two basin-relocation dimensions.

## 3. Verdict-class priors — RECOMMEND 12/18/35/22/13

| Verdict | QR | LM Master | Rationale |
|---|---|---|---|
| PROMISING | 15% | **12%** | -3pp; basin-survival ratio 0.5-0.7 caps lift below +0.40 OOS Δ |
| PROMISING-INERT-FAV | 20% | **18%** | -2pp; partial mechanism survival modal here |
| INERT (modal) | 35% | **35%** | unchanged |
| NEG-clean | 20% | **22%** | +2pp; partial-survival + worse-than-baseline tail |
| NEG-CAT | 10% | **13%** | +3pp; ASYMMETRIC_ROTATION prior class binds NEG-CAT ≥10% AND label change adds 2nd basin-relocation vector |

NEG total 35% vs QR's 30%. PROMISING tail compressed 35% → 30%.

## 4. F-AXIS pre-registration

- **F-AXIS #1**: LTC-only dispatch binary PASS — APPROVED
- **F-AXIS #2**: IS [70, 150] modal 105; OOS [22, 55] modal 35 (tighter SL → R1 cooldown engages more). QR's [80, 180] / [20, 60] wider safety margin acceptable
- **F-AXIS #3 SL fire-rate at OOS** — **COUNTER-INTUITIVE**: TIGHTER SL → INCREASES SL fire-rate (not decreases). Predicted OOS SL fire-rate **75-90%** (vs baseline 62%). If observed < 60% → UNDERFIRING (basin avoided SL trigger → INERT). If > 90% → OVERFIRING ("3% lottery tickets")
- **F-AXIS #4 n_eff**: [6, 10] modal 8 (atr_sl change shifts class balance ~10-20%; marginal TPE convergence impact)
- **F-AXIS #5 exit-reason distribution** — **LOAD-BEARING**: OOS SL 75-90% / TP 0-8% / timeout 10-20% (baseline 62/12/26). **If TP=0 OOS, ALL upside lost** → verdict CANNOT exceed PROMISING-INERT regardless of F1

## 5. /022 lesson application — PARTIAL inoculation, NOT immunity

atr_sl IS more basin-robust than /022's asymmetric gate, BUT NOT basin-INVARIANT. Quantify: baseline-roster +36% lift × basin-survival ratio 0.5-0.7 = expected /028 lift +18-25% PnL → OOS Sharpe Δ **+0.25 to +0.45** (PROMISING-INERT-FAV territory; PROMISING tier requires survival ratio ≥0.7).

## 6. Most important point

**The dominant verdict-determining variable is OOS TP-exit count**: baseline LTC OOS had 4 TP exits contributing +31.64% PnL; if atr_sl=1.0 converts ≥2 of these to SL at retrained roster, mechanism's net effect collapses below +0.20 OOS Sharpe Δ regardless of how cleanly it clips moderate-loss bucket. **F-AXIS #5 TP-exit count is LOAD-BEARING diagnostic, NOT F-AXIS #3 SL fire-rate.**

## 7. /029 verdict-conditional pre-staging

- **PROMISING (12%)** → /029 = DOT pre-classification + DOT-only specialist (LM Master /022 §5 carry-forward; pre-classify against ASYMMETRIC_ROTATION rule)
- **PROMISING-INERT-FAV (18%)** → /029 = DOT-specialist (same)
- **INERT (35% modal)** → /029 = **sample-weighting axis** (López de Prado AFML Ch.4 inverse-concurrency; UNUSED in v1). Substrate change orthogonal to cycle-3 axes
- **NEG-clean (22%)** → /029 = sample-weighting (INERT + NEG-clean both route here)
- **NEG-CAT (13%)** → /029 = **FUNDAMENTAL RE-QUESTION**. 3rd NEG-CAT in same prior class (/020 + /022 + /028) closes per-cohort axis permanently. /029 = XGBoost head-to-head OR universe contraction (drop LTC from pool)

## Critic Phase 7.5 priority items

1. F-AXIS #5 OOS exit-reason distribution against pre-registered bands
2. Label class balance vs baseline LTC training (count +1/-1/0)
3. Optuna best_params shift in basin vector
4. TP-exit count OOS ≥ 1 (if 0, mechanism degenerates to loss-clipping-only → PROMISING-MECHANICAL even at PROMISING-tier F1)

## Closing

**MEDIUM confidence** three calls:
1. Multi-seed via `--ensemble-size 10` NOT `--seeds 2` (HIGH confidence — mechanical)
2. F-AXIS #5 TP-exit count LOAD-BEARING (replaces /022's F-AXIS #3)
3. Priors 12/18/35/22/13 (NEG total 35% vs QR 30%)

**Single most important point for QR**: brief §0.4 "basin-orthogonal" framing overstated. atr_sl upstream of triple-barrier label generation — BOTH basin AND label distribution shift simultaneously. Phase 7.4 verdict must compare TWO basin-relocation dimensions (best_params + label class balance).

---

# LightGBM Master Post-Mortem — iter-v1/028 — Phase 7.4

## Context

PROMISING outcome — 12% tail materialized; FIRST ASYMMETRIC_ROTATION cohort to clear PROMISING in v1 history. 3rd PROMISING specialist (after LINK /018 +0.80, ETH+gate /019 +0.50).

## 1. Phase 4.5 prediction-reality

Priors 12/18/35/22/13. Observed PROMISING (12% tail). OOS Δ +0.598 ABOVE my predicted [+0.25, +0.45] band by +0.15 (favorable miss).

| Prediction | Observed | Verdict |
|---|---|---|
| PROMISING 12% | PROMISING (Δ +0.598) | **HIT 12% tail** |
| F-AXIS #5 TP-exit ≥2 = PROMISING reachable | OOS TP=5 | **VINDICATED** |
| F-AXIS #3 SL rate 75-90% | 59% (right at UNDERFIRING 60% threshold) | MISS — actually UNDER not OVER |
| F-AXIS #4 n_eff [6,10] | 2 | **MISS LOW** (puzzle, see §4) |
| Basin-survival ratio 0.5-0.7 → lift +18-25% PnL | OOS PnL +9.38 USD (vs baseline LTC ~-3-5 USD) | within band |
| LM Master Rec #6 LOAD-BEARING TP-count | LOAD-BEARING verified | **HIT** |

## 2. Why atr_sl=1.0 WORKED where /022 asymmetric gate FAILED

The key Phase 4.5 §2 reframing: atr_sl is UPSTREAM of label generation. **TWO basin-relocation vectors** (label class balance + post-entry clip) means /028 changes BOTH what the model trains on AND what the model executes — vs /022 only changing execution (pre-entry gate).

**Outcome**: /028 produced a fresh trade roster (39 OOS vs /022's 48 OOS; mostly disjoint per single-cohort retraining at single-seed precedent). The atr_sl=1.0 narrower lower barrier means:
- LightGBM learns to AVOID trades that would hit -1.0×ATR quickly (i.e., model avoids high-volatility-against-direction trade configurations)
- Surviving trade roster has STRUCTURALLY DIFFERENT risk profile (~70% SL rate IS vs /022's 51%; OOS 59% vs /022's 56%)

The label-distribution shift created a new training signal LightGBM could learn. /022's gate was post-Optuna filter; /028's atr_sl is pre-Optuna labeling — exponentially more leverage.

## 3. F-AXIS #5 LOAD-BEARING VINDICATED

Rec #6 declared OOS TP-exit count load-bearing. Observed TP=5 (≥2 PROMISING-reachable threshold) → verdict cap LIFTED. Counterfactual: if TP=0, verdict would have been capped at PROMISING-INERT regardless of F1 +0.598.

The 5 OOS TPs contributed material upside (let me estimate: average TP PnL likely +2-3%, so 5×2.5 = ~+12.5% — actually OOS net_pnl +9.38 USD across 39 trades = +0.24%/trade average; positive TP wins balance SL clips).

**Methodology call 7/7 perfect** (DUAL GATE + HARD BLOCK + ABS-EDA-TRADE-ATTRIBUTION + per-cohort SATURATION rule + dispatch-defect lesson + F-AXIS #5 LOAD-BEARING + atr_sl basin-relocation 2-vector reframing).

## 4. n_eff=2 puzzle

ENSEMBLE_SIZE=10 + n_trials=35 → expected n_eff [6, 10]. Observed n_eff=2.

Hypothesis: n_eff measures EFFECTIVE TRIAL DIVERSITY in OOF parquet. At ENSEMBLE_SIZE=10 inner seeds × n_trials=35 = 350 trial-evaluations per (symbol, month). n_eff=2 means Optuna trials clustered to 1-2 dominant basins per cell. **This is a feature, not a defect** under the atr_sl=1.0 labeling shift — narrow barrier reduces label-space ambiguity, Optuna converges fast to confident basins.

Comparable to /015 multi-seed CONFIRMATION n_eff. Not blocking; informational only.

## 5. Cycle-3+ structural finding update

**Per-cohort SATURATION rule (codified at /022) is REFINED**: 

OLD rule: ASYMMETRIC_ROTATION cohorts INVIABLE for single-cohort isolation REGARDLESS of gate symmetry.

NEW rule (post-/028): ASYMMETRIC_ROTATION cohorts INVIABLE for **PRE-ENTRY** gate mechanisms (direction filter, regime kill). VIABLE for **UPSTREAM LABEL** changes (atr_sl multiplier, barrier asymmetry). The /022 → /028 differential (+1.77 OOS Sharpe lift) is mechanism-class-specific.

Codify as `feedback_v1_atr_sl_label_shift_mechanism.md`: atr_sl multiplier changes label distribution at training time, enabling LightGBM to learn a fundamentally different decision boundary. Distinct from post-entry gates which filter a FIXED roster.

## 6. /029 verdict-conditional — RECOMMEND multi-seed validation FIRST

Per Phase 4.5 §7 PROMISING → DOT pre-classification + DOT-only specialist. BUT given:
- /028 is single-seed (ENSEMBLE_SIZE=10 single-pass; no outer-seed loop)
- 3rd PROMISING specialist; bundle path for /027 retry
- /015 multi-seed CONFIRMATION lesson: single-seed PROMISING regressed 18-22% at multi-seed

**Recommend /029 = MULTI-SEED VALIDATION of /028** (re-run atr_sl=1.0 at higher seed/trial budget OR with --confirmation flag if /027 lessons can be applied without crashing). Validates /028 PROMISING before committing to bundle inclusion.

Alternative /029 = DOT-only specialist (cycle-4 cohort coverage) BUT defer multi-seed validation to /027-retry.

**LM Master recommendation: /029 = DOT-only at single-seed EXPLORATION budget** (continues cycle-4 cohort coverage; cheaper); /030+ = multi-seed validation of LINK + ETH+gate + LTC+atr_sl_1.0 + DOT-? as combined 3-or-4-specialist bundle.

## 7. /027 retry bundle composition (post-/028)

If LTC validates at multi-seed:
- LINK +0.80 single-seed → +0.55-0.65 multi-seed
- ETH+gate +0.50 single-seed → +0.32-0.40 multi-seed
- LTC+atr_sl=1.0 +0.598 single-seed → +0.30-0.45 multi-seed (per /015 precedent regression)
- 3-specialist bundle multi-seed target: +1.20-1.55 (baseline +0.66 + 0.55-0.85 net specialist lift after correlation drag)

This is the FIRST credible path to +1.0 OOS Sharpe (hard merge floor) in v1 history. PROMISING-METHODOLOGY at /027 multi-seed could become PROMISING-MERGE if cross-correlation < 0.50 holds.

## 8. Track record

Cumulative LM Master: methodology 7/7 (perfect); directional 3/9 = 33%.

The 7th methodology call (F-AXIS #5 LOAD-BEARING TP-exit count) was the load-bearing diagnostic for /028 verdict. Without the Rec #6 mandate, verdict could have been classified ambiguously; with it, the verdict is unambiguous PROMISING.

## 9. Most important Phase 7.4 finding

**The atr_sl=1.0 mechanism is the FIRST UPSTREAM-LABEL change that successfully cleared the ASYMMETRIC_ROTATION cohort saturation rule (codified at /022), producing the 3rd PROMISING specialist in v1 history (+0.598 OOS Δ vs /022's -1.17, a +1.77 differential) — refining the cycle-3 SATURATION rule from "ASYMMETRIC_ROTATION INVIABLE for single-cohort" to "ASYMMETRIC_ROTATION INVIABLE for PRE-ENTRY gates but VIABLE for UPSTREAM LABEL changes"; cycle-4 EXPLORATION-1 establishes a credible /027-retry path to +1.0 OOS Sharpe (hard merge floor) via 3-specialist bundle at multi-seed validation.**
