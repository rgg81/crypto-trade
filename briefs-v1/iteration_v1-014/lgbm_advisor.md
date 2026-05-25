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
