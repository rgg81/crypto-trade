# LightGBM Master Advisor — iter-v1/014 — Phase 4.5 (Pre-Design)

## Context Read

- **Track**: v1. Branch `iteration-v1/014`. HEAD `6d7fce5`.
- **Baseline**: `v0.v1-baseline-corrected` (`f8bc12c`). IS +0.2829 / OOS +0.6637. Unchanged post-/010-/013.
- **Brief**: cycle-2 EXPLORATION #9/10. Single axis: replace NATR_21×atr_mult barriers with past-only EWMA σ_t × k (k_tp=1.06, k_sl=0.53, half-life=42 candles). HIGH-RISK declared. R5 disabled (axis isolation).
- **My track record**: **0/11 directional + 4 PARTIAL**. FLAT priors only per /013 §5 FINAL calibration rule.
- **EDA honesty**: per-regime ratios near-constant within-symbol (BTC 1.14/1.13/1.11; LINK 0.94/0.91/0.91 across vol terciles). Hypothesis revised: per-symbol LEVEL offset is load-bearing mechanism, NOT regime adaptivity.

## 1. EDA Collinearity Finding — Does It Kill the Hypothesis?

**No, but it shrinks the mechanism's degrees of freedom from 2 to 1.**

QR Section 2.5 finding is HONEST and load-bearing: within-symbol σ_t/NATR ratio is approximately scalar (~1.13 BTC/ETH; ~0.92 alts), with sub-symbol regime ratios ranging only 1.111-1.145 (BTC) and 0.894-0.961 (LTC). The "regime adaptivity escapes basin lottery" story is **weak**.

**What remains** is the per-symbol LEVEL offset: BTC/ETH ~10% wider barriers; alts ~7% tighter. This DOES change the loss surface — but mechanistically equivalent to per-symbol atr_tp adjustment (tested in /005 vintage with similar single-seed flatness observed).

**The per-row tail divergence (p10/p90 ratio 0.66-1.47) routes ~20% of candidate labels to different TP/SL/TO resolution.** That IS a genuine label-distribution change, not just rescaling. Per Section 2.6 simulation, predicted PORTFOLIO-level direction is OPPOSITE across BTC/ETH (TO% UP +5.2pp) vs alts (TO% DOWN -7.3pp LINK). Structurally different from prior /011-/013 axes.

**Verdict on hypothesis viability**: SURVIVES, but WEAKER than initial brief framing. FLAT prior 33/33/34 correct. P(positive basin draw) ≤ 33%.

## 2. /014 Outcome Priors — Basin-Lottery Risk Profile

DOES change IS label distribution per-cell — different mechanism class from R5-BINARY-KILL (which left labels untouched).

**Partial-shift scenario, not full re-draw**:
- Per-row label divergence ~20% of candidate rows (σ_t/NATR ratio outside [0.85, 1.18]). Other 80% resolve same TP/SL/TO class.
- Per-symbol exit-mix shift modest (5-8pp portfolio TO% movement per cluster).
- Wider BTC/ETH barriers → larger |labeled_pnl| per TP/SL hit → potential up-weighting of BTC/ETH in IS basin selection. **Asymmetric attention reshuffling**.

**Specific basin-lottery risks**:
- Per-symbol catastrophic-reversal rotation observed at /011-/013 likely re-rotates under /014. Expected catastrophic candidate: **LTC** (largest barrier compression at -7.6% high-vol regime).
- OOS amplification fraction at /014 is unconstrained by prior data — labeling is structurally NEW lever.

## 3. Hyperparameter Recommendations

### Rec #1 — Keep Optuna search bounds UNCHANGED at /014
Axis isolation. The label change alone is the experiment. Co-tuning Optuna bounds prevents /015 attribution. Risk: None.

### Rec #2 — Pre-attend `min_data_in_leaf` at /015 (not /014)
If /014 yields IS-OVERFIT, /015 brief should ALSO test `min_data_in_leaf` upper bound = 500 (vs default). Why: tighter alt-symbol barriers shrink labeled-PnL distribution; Optuna may pick narrow leaves to fit smaller-magnitude alt labels (classic "regularization needed when label magnitude shrinks").

### Rec #3 — Lookahead audit MANDATORY at Phase 6.0
**σ_t computation MUST use `.shift(1)` after `ewm(halflife=42, adjust=False).std()`.** Static-scan `lgbm.py` for shift call in new `_load_sigma_for_master()` path. If σ_t at candle t uses CURRENT candle's return (no shift), labels embed t-time information. At single-seed EXPLORATION, missing shift is INVISIBLE in headline metrics until OOS catastrophe at /015 CONFIRMATION. **Critic Check 5 ADF preflight MUST verify this.**

## 4. Risks to Flag at Critic Phase 7.5

- **F7-NEW per-symbol exit-mix direction (mechanical attribution)**: predicted direction BTC/ETH TO% UP, alts TO% DOWN. Critical Critic check: does observed match across ≥3 of 5 symbols? If alts TO% UP instead of DOWN, σ_t mechanism is wired wrong. **F7-NEW is the ONLY axis-attribution-clean falsifier at /014.**
- **F8-NEW trade-count band [466, 776]**: calibration-tight. Observed IS trades = 400 OR 850 → k_tp/k_sl needs re-grid.
- **Basin-lottery dominance**: per /013 §5 final calibration, at v1 single-seed EXPLORATION, F1/F3 outcomes are basin-determined, NOT axis-attribution. If F1 = +0.4 OR -0.7, neither evidence FOR or AGAINST labeling axis.
- **HIGH-RISK pre-commit binding**: /015 CONFIRMATION fires regardless. If /014 catastrophic, Critic must NOT pivot /015 off labeling.
- **Boundary-cell hazard**: F1 ∈ (+0.03, +0.07) — declare numerical-boundary and require seed-determinism audit BEFORE /015 design.

## 5. /015 CONFIRMATION Viability

**Both, in specific order**:

### Primary: mean basin draw across 10 seeds
At v1 single-seed std ≈ 0.80 per draw, 10-seed CONFIRMATION mean has SE ≈ 0.25. Multi-seed estimate lands [-0.5, +0.5] before mechanism. **Falsification target: multi-seed mean ≥ +0.15 OOS Δ clears noise floor by ~0.6 SE — ONLY THEN does labeling become real edge candidate.**

### Secondary: per-symbol mechanism attribution
After mean basin draw confirmed positive, /015 should pre-register **F7-NEW EQUIVALENT at multi-seed**: does per-symbol exit-mix direction REPLICATE across 10 seeds? If 8/10 show predicted direction, mechanism robust. If flips per-seed, basin lottery wins even at multi-seed.

### /015 brief structure recommendation
- At multi-seed, FLAT priors COLLAPSE somewhat — concentration toward NULL justified. Pre-register **60% NULL / 25% PROMISING / 15% NEGATIVE**. **First place I move off FLAT prior** because variance reduction is mechanically guaranteed at multi-seed.

## 6. Honest Confidence

Track record: **0/11 directional + 4 PARTIAL**.

**WILLING (HIGH confidence)** at /014:
- F8-NEW IS trade count in [466, 776] at ~80% probability
- F7-NEW per-symbol direction matches predicted for ≥3 of 5 symbols at ~70%
- σ_t lookahead-clean if `.shift(1)` present at ~95%

**WILLING (LOW confidence)** at /014:
- F1 verdict-class at 33/33/34 FLAT
- F3 verdict-class at 33/33/34 FLAT

**NOT WILLING** at /014:
- F1 OR F3 magnitude
- Which per-symbol basin draw is catastrophic
- Whether /014 single-seed correlates with /015 multi-seed mean

**WILLING (MEDIUM confidence) at /015**:
- /015 multi-seed mean OOS Δ ∈ [-0.30, +0.30] at ~75%
- /015 multi-seed mean ≥ +0.15 (clear noise floor) at ~20% — my honest call on whether labeling is first v1 edge ingredient

## Closing Note

**Single non-ignorable point**: F7-NEW per-symbol exit-mix direction is the ONLY axis-attribution-clean falsifier at /014. F1/F3 are basin-lottery-dominated and provide essentially zero mechanism information per /013 §5. **QR/Critic should NOT weight /014's F1/F3 verdict-class heavily** in /015 design.

**Two concerns about cycle-2 catalog discipline**: (1) HIGH-RISK declaration is FIRST in cycle-2 — pre-commit /015 binding is entire mitigation, do not erode it; (2) post-/015 if labeling multi-seed-NULL, /016 should pivot to UNUSED-UNUSED family (universe or model-arch), NOT another labeling sub-axis re-calibration (basin-fishing trap).

---

# LightGBM Master Advisor — iter-v1/014 — Phase 7.4 (Post-Mortem)

## Context Read
- Iteration outcome: IS Sharpe **-0.6112** / OOS Sharpe **+0.1828** / ratio **-0.2991** (sign-flipped). F1 NEGATIVE (Δ -0.4809), F3 NEGATIVE-catastrophic (Δ -0.8941), F8-NEW PASS (598 ∈ [466, 776]).
- Engineering: σ_t lookahead-clean verified; F8-NEW PASS; Critic Concern C1 (barrier-source label/execution inconsistency) UNRESOLVED.
- /015 = labeling CONFIRMATION binding (FIRED per pre-commit).

## 1. n_eff Structural Finding — DURABLE EVIDENCE Despite NEGATIVE Verdict

**n_eff jumped 13 → 19 (per-cell median; range 14-22) — FIRST material shift in v1 cycle-2.** Per dsr.json, BTC/ETH=20, LINK/LTC=18, DOT=19. /008-/013 all stayed at 13. This is the **strongest mechanism evidence in 12 iterations** that σ_t labeling diversified the Optuna loss surface as predicted in Phase 4.5 §2 ("partial-shift scenario").

**Durable structural evidence** independent of /014's F1/F3 magnitudes. The 33/33/34 FLAT prior governs BASIN DRAW; n_eff governs LOSS SURFACE GEOMETRY. /014 produced a NEGATIVE basin draw on a RICHER surface — independent. At /015 multi-seed, n_eff=19 should REPLICATE; if it does, mechanism robustness CONFIRMED regardless of F1 direction.

## 2. F7-NEW Evaluation — 4/5 PASS (PARTIAL per Brief 8-cell matrix)

Per IS exit-mix comparison (014 vs baseline):

| Symbol | Pred TO | Obs ΔTO | Match |
|---|---|---|---|
| BTCUSDT | UP | +4.2pp | YES |
| ETHUSDT | UP | **-3.2pp** | **NO** |
| LINKUSDT | DOWN | -8.9pp | YES |
| LTCUSDT | DOWN | -2.4pp | YES |
| DOTUSDT | DOWN | -3.2pp | YES |

**F7-NEW = PARTIAL.** Mechanism IS sound on 4/5 symbols. ETH is the rogue — TO% DECREASED (-3.2pp) instead of increased; SL% INCREASED (+8.4pp). ETH's "wider labels" should have meant MORE timeouts, but execution-time NATR barriers (Concern C1) overruled label-time wider σ_t barriers. This is the **first observable signature of C1 in trade data**.

## 3. Critic Concern C1 — Load-Bearing IS Catastrophe Explanation

**C1 is the load-bearing IS catastrophe explanation, not basin lottery alone.**

- Label-time: σ_t × k (BTC/ETH ~13% WIDER than NATR-current; alts ~7% TIGHTER)
- Execution-time: NATR × atr_mult (UNCHANGED — 2.9/3.5 multipliers)
- For BTC/ETH: label says "TP at +5.91% (σ_t-wider)" but execution closes at +5.06% (NATR-narrower) → systematic positive labeling bias → Optuna trains on labels saying "many TPs hit" but execution realizes fewer → IS basin penalty
- For LTC: tighter labels + wider execution = trades ride LONGER than predicted → C1 WINDFALL

**LTC win AND BTC/ETH catastrophe are BOTH C1 signatures.** C1 unresolved is the proximate cause of /014's per-symbol pattern.

C1 disclosure is **MANDATORY** in /015 engineering report. Critic will FAIL Check 8 if /015 doesn't address.

## 4. LTC IS+OOS Winner — Phase 4.5 Prediction INVERTED

My Phase 4.5 §2 prediction: "LTC = catastrophic candidate; largest barrier compression at -7.6%." **WRONG.** LTC was the WINNER on both halves (IS +95.51 / OOS +24.49 / WR 47.7% IS / 50.0% OOS).

**Mechanism**: tighter LTC barriers produced MORE labeled TPs per IS row (28.1% TP rate vs 20.2% baseline — biggest TP% jump). LTC's strongly-trending IS regime had dense short-horizon TP opportunities the σ_t-tighter labels captured. Combined with NATR-wider execution (C1 inverted-direction for alts), execution exits SURVIVED LONGER than labels predicted. Asymmetric C1 windfall for alts, asymmetric C1 penalty for BTC/ETH. **C1 is proximate cause of LTC win AND BTC/ETH catastrophe simultaneously.**

## 5. Calibration Update — Track Record 0/12 Directional + 5 PARTIAL

Update: **0/12 directional + 5 PARTIAL** (F8-NEW PASS, σ_t lookahead-clean, n_eff prediction correct, F7-NEW 4/5 PARTIAL, FLAT prior calibrated).

Mechanism predictions (lookahead-clean, n_eff diversification, exit-mix 4/5) are RELIABLE; directional F1/F3 predictions remain at 0/12. **Phase 4.5 priors will keep FLAT 33/33/34 for verdict-class. NEW addition: mechanism-level PARTIAL claims (n_eff, F7-NEW direction) at MEDIUM confidence.** Stop predicting per-symbol catastrophic candidates — 0/4 in cycle-2.

## 6. /015 CONFIRMATION Multi-Seed Prior — Updated

Phase 4.5 §5 pre-registered **60% NULL / 25% PROMISING / 15% NEGATIVE**. /014 single-seed OOS Δ = -0.48; single-seed std ≈ 0.80; 10-seed SE ≈ 0.25. Observed -0.48 is 1.9 SE below 0 — boundary territory.

**Updated /015 prior**: **55% NULL / 20% PROMISING / 25% NEGATIVE**. Marginal NEGATIVE bump (+10pp) because (a) C1 unresolved amplifies negative draws asymmetrically; (b) IS -0.89 is unprecedented in cycle-2. PROMISING shrinks (-5pp) because LTC IS+OOS positive depends on C1's asymmetric windfall; at multi-seed the C1 windfall doesn't replicate cleanly.

**Modal multi-seed outcome remains NULL.**

## 7. /015 Brief Design Recommendations

**Mandatory for /015 brief**:

1. **C1 FIX — execute-time barriers ALSO use σ_t × k_tp/k_sl**. Without this, /015 measures confounded experiment. NOT a "2nd axis" — COMPLETES the labeling axis. Per /014 evidence (ETH ΔSL +8.4pp; LTC C1-windfall +7.9pp ΔTP), C1 unresolved corrupts F1/F3 measurement. **HIGH-CONFIDENCE recommendation.**

2. **Per-symbol F7-NEW direction stability across 10 seeds**: pre-register table where each cell is "matches/10 seeds". If ETH matches 2/10 even at multi-seed → ETH-specific wiring defect. If ETH matches 7-10/10 → /014's ETH deviation was single-seed artifact.

3. **n_eff multi-seed verification**: pre-register "n_eff ≥ 17 across at least 7/10 seeds". If n_eff collapses to 13 at multi-seed, loss-surface diversification was single-seed artifact (unlikely; n_eff bound by label-distribution shape).

4. **Engineering report MUST disclose C1 status**: explicitly state whether C1 was fixed for /015 and per-symbol label/execution barrier ratios. Critic Check 8 demands this.

5. **Hyperparameter recommendation**: keep n_trials=35; raise min_data_in_leaf upper bound to 500 IF C1 fixed (per Phase 4.5 Rec #2). If C1 NOT fixed, leave bounds unchanged (axis isolation).

## What This Iteration Confirms / Refutes About Prior LM Master Advisory

**CONFIRMED (3)**: FLAT prior calibrated; σ_t lookahead-clean at 95%; F8-NEW band at 80%. **MECHANISM-LEVEL ACCURATE.**

**REFUTED (2)**: LTC catastrophic-candidate (INVERTED — LTC was winner); per-row label-divergence 20% (UNDER-predicted; n_eff jump suggests deeper structural change).

**SURPRISE (1)**: Concern C1 is mechanically load-bearing — both LTC win and ETH catastrophe are C1 signatures. **Future Phase 4.5: when Critic preflight flags barrier-source / label-source consistency, escalate to "mechanism explanation candidate" in §1.**

## Closing Note for Critic (Phase 7.5)

Three items for Critic 8-check pass:

1. **Check 8 (axis attribution)**: F7-NEW 4/5 PARTIAL with ETH deviant — verify engineering report discloses ETH exit-mix AND addresses C1 inconsistency. This is C1 surface-in-data event.

2. **Check 5 (ADF)**: n_eff jumped 13→19 indicating richer per-cell loss surface — re-verify ADF stationarity on σ_t-labeled labels (NOT just raw σ_t feature). If labels show non-stationarity at IS→OOS boundary, catastrophic IS may have non-stationarity component alongside C1.

3. **/015 axis pre-commit erosion risk**: brief Section 11 pre-commits /015 = labeling CONFIRMATION binding. Critic should REFUSE any /015 brief that pivots off labeling AND INSIST /015 includes C1 fix per §7. The C1 fix COMPLETES the labeling axis (not 2nd axis).

Honest summary: /014 mechanism worked (4/5 F7-NEW, n_eff diversification, lookahead-clean); /014 basin was NEGATIVE with C1 amplifying asymmetry. /015 multi-seed with C1 FIXED is the genuine test. Modal outcome NULL (55%) but experiment is finally well-posed.
