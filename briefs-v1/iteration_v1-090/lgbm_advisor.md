# LightGBM Master Advisory — iter-v1/090 (W-DECAY)

Anchor BUNDLE-002 v0.v1-082 (IS +0.7157/OOS +1.0043). Test seat ETH/064 (IS +0.2383/OOS +0.5171). LOCK: 50 seeds × 30 trials × depth-5 × leaves-31 × 24mo; half-life 12mo; single seat; no multi-seed. All advisory.

## 0. CRITICAL — decay and training_days COMPOSE, they do NOT substitute
Code path: `(b3)` lgbm.py:892-899 computes `decay=exp(-ln2/12·age_months)` over the FULL train window ONCE, folded into train_weights BEFORE Optuna. Inside each trial, optimization.py:392 trims train_idx to the last `training_days`, then :417 `w_train=w[train_idx]` — **decayed weights survive the trim**. So a trial picking training_days=120 trains on the last 120d WITH decay still applied (in-window oldest ≈ exp(-ln2/12·4)≈0.79). Decay does NOT replace truncation — it STACKS on whatever window Optuna picks. **The brief's "removes Optuna's incentive to collapse training_days" is SECOND-ORDER, not first-order.** Consequence: F2 fires WEAKLY at best; the brief's "median toward/above 500d cap" is mechanically over-stated. **A correct W-DECAY can produce F1>0 with F2-flat** — which the brief's bands would mis-tag NEGATIVE-INERT. (QE: confirm trim-after-decay ordering is intended — it is defensible AFML Ch.4 decay-within-window.)

## 1. Sample-weight mechanics
- **(a) is_unbalance×decay:** orthogonal axes (is_unbalance = per-class count multiplier; sample_weight = per-row), multiply cleanly, NO double-count. BUT decay×is_unbalance shifts the EFFECTIVE class balance if recent data is class-skewed → F1 partly reflects class-rebalancing. Log long/short WEIGHT share vs the label-balance print.
- **(b) abs_pnl×decay:** no recency double-count, but COMPOUNDS dispersion → effective sample size drops twice (Kish ~0.5-0.6 → **0.35-0.45**; 198 ETH IS trades behave like ~75 effective). ESS shrink is an overfit amplifier; the 50-study mean does NOT offset it (different variance source than basin-lottery). Watch the `_kish_ratio` log.
- **(c) NORMALIZATION (STRONGEST REC):** brief says "no renormalization" — mechanically a flag. Un-renormalized decay multiplies total weight MASS by mean(decay)≈0.55, which HALVES `min_child_weight`'s bite (it's in absolute weighted units) → **stealth regularization loosening** (trees grow finer on recent data). So un-renormalized decay does TWO things: recency (intended) + regularization-loosening (unintended). **A VALIDATED F1 is UNATTRIBUTABLE between recency and the reg side-effect without a log.** REQUIRED (advisory→QE): add ONE log line at `(b3)` of `decay.mean()` + `train_weights.sum()` pre/post-decay so Phase 7.4 can split the channels. (Renormalize-to-mean-1 would isolate it cleanly, but the lock pins the impl — at minimum the log.)

## 2. Half-life 12mo
At 12mo/24mo oldest retains 0.25 (4:1) ACROSS the full window — but per §0 the model trains on a ~4-8mo TRUNCATED window where the in-window decay spread is only ~exp(-ln2/12·6)≈0.71 (gentle 1.4:1). Too soft to reshape the in-fold objective much. 12mo is the right CONSERVATIVE first-probe value (avoids the 9mo "mimics truncation" trap) but gentle → expect F1 in the TENTATIVE [0.00,+0.20) band, not VALIDATED. Concur with QR modal.

## 3. F2 mechanistic prediction (PRE-REGISTERED, REVISED SCALE)
- Direction: LONGER, F2 FIRES — but WEAKLY.
- **Magnitude point estimate: ETH median training_days rises ~30-60d** vs the abs_pnl control (NOT cap-ward). Folds<120d drops ~10-20pp, not to zero. Modal ~180d→~220-240d.
- If median jumps >150d or hits the cap → SUSPECT the §1c reg-loosening changed the loss landscape, not pure recency.
- **LOAD-BEARING: a null F2 (no shift) can be CORRECT, not a bug** (decay stacks, doesn't substitute). The brief's "Sharpe lift WITHOUT training_days shift is NOT evidence" guard is sound BUT may mis-classify a real-but-small recency effect as inert. **Read F2 magnitude on the REVISED small scale; do NOT auto-tag NEGATIVE-INERT if F1>0 but F2 is weakly-positive/flat — that is a falsifier-design tension to resolve at Phase 7, not a mechanism failure.**

## 4. Per-seed dispersion
Decay shifts the objective surface NON-uniformly across the 50 TPE seeds (seed-path-dependent training_days×lr search). The Kish drop (§1b) is seed-invariant → hits all 50 equally → the mean is NOT protected against ESS shrink. If decay helps some seeds (longer window) and hurts others (ESS shrink), the mean-of-signed-weights aggregator could WASH the effect to ≈0 (F1-INERT masking a bimodal effect). Log per-seed training_days STD (not just median) at 7.4.

## 5. Risks
1. **INVERSE-EDGE (the big downside, ~25-30%):** if ETH's IS edge lives in 2022-23 (bear→recovery), recency-weighting DISCARDS the signal-bearing samples → F1 NEGATIVE. Most likely path to outright F1<0. Can't rule in/out from IS-only artifacts.
2. Uniqueness double-penalty NOT active (`(b2)` dormant for the abs_pnl ETH seat) — drop this concern for /090.
3. §1c reg-loosening confound — restated: VALIDATED F1 could be the stealth min_child_weight loosening, not recency. UNFALSIFIABLE without the §1c log. Strongest single rec.

## Closing
Confidence iteration improves ETH: LOW-to-MEDIUM. Modal TENTATIVE (~50%), VALIDATED upside (~20%), NEGATIVE tail (~25-30%, inverse-edge). **QR must not ignore §0 (compose-not-substitute → F2 weak, second-order) + §1c (add the decay.mean/weight-sum log or F1 is unattributable).**
