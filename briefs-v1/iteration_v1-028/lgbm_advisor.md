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
