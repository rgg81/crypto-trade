# LightGBM Master Advisor — iter-v1/084 — Phase 4.5 (Pre-Design)

## Context Read
- Track: v1. Methodology LOCKED: `v1_specialist` profile — `max_depth=5` FIXED, `num_leaves=31` FIXED, 50 seeds × 30 trials × ENSEMBLE_SIZE=1/seed, ATR 2.9/1.45, R3-only (Model A pattern). I do NOT touch this. All advice below is feature/risk-layer, inside the lock.
- Baseline: BUNDLE-002 (`v0.v1-082`) — DOT/063 + ETH/064 + BTC/065 + AAVE/078; IS +0.7157 / OOS +1.0043. CRV does not overlap the bundle (pairwise-disjoint PASS); not in V1_EXCLUDED.
- Prior iter /083 outcome: FIL specialist NEGATIVE-MOMENTUM-DOMINATED — trivial TS-momentum IS +1.45 left ML zero headroom (ML IS −0.82). The reform is correct: trivial baseline, not narrative orthogonality, predicts headroom.
- Reformed-selection target: CRVUSDT, min-horizon trivial IS Sharpe **+0.069** (50d), the lowest of 12 candidates (next-best GALA +0.627; ARB +0.005 disqualified at <4y if its full extent gate failed — CRV is the cleanest ≥4y MEDIUM). Bear-regime trivial **−0.924** is the real prize: trivial momentum is systematically wrong in CRV bear regimes — that is exactly where a non-linear head has room.

## Recommended Hyperparameter Direction

**None within the lock — and that is the correct call.** The methodology is frozen at `max_depth=5`/`num_leaves=31`/50-seed/30-trial by user directive, and CRV's training profile does not argue for breaking it: IS rows are single-symbol (~4995 IS bars × 24-mo walk-forward windows ≈ 1.5–2.0k rows/cell), well inside the capacity that `num_leaves=31` at `min_data_in_leaf`-default serves without starving leaves. The 50-seed inner ensemble is the variance control that makes single-seed basin-lottery a non-issue here (the failure mode that killed BTC/065 + DOT at single-seed EXPLORATION in cycle-6). Holding the lock is the right hyperparameter decision, not an omission.

One observation for the post-mortem, NOT an action now: CRV NATR p50 = 7.885% is materially HOTTER than DOT/AAVE (~4–5%), with p90 = 10.0%. At fixed ATR 2.9/1.45 the SL distance scales with realized ATR, so this is self-normalizing — but watch the run.log best-trial `learning_rate` / `n_estimators` spread across the hot 2022 months. If best `n_estimators` pins at the 500 cap in the high-vol cells, that is a capacity signal to flag at /085, not to fix now.

## Recommended Feature-Engineering Direction

### 1. `oi_price_divergence_30` — already committed; my read is GO, with one caveat
- **What**: `z90( sign(oi_delta_30) − sign(ret_30) )`, past-only via `.shift(1)`, clipped [−10,+10]. Re-aimed from the /083 OI family (oi_delta_30_z90 rank 7/49; fil_oi_price_divergence_30 rank 11/49) onto a NEGATIVE-baseline symbol — binding the signal to the feature, not the symbol. Correct application of the /083 learning.
- **Why this is NOT redundant with `oi_delta_30_z90`**: the sign-difference operator is the key. `oi_delta_30_z90` is a continuous magnitude z-score; this feature quantizes both legs to {−1,0,+1} and z-scores the {−2,0,+2} disagreement. Magnitude is discarded; only directional CONFLICT survives. Empirical Pearson IC against `oi_delta_30_z90` should land well under 0.50 — this is a genuinely new column, not a Category-2 algebraic sister. (Contrast: it would have been redundant had it been `oi_delta_30 × ret_30` continuous.)
- **IC pre-warning**: expect |IC| with the closest primitive (`oi_delta_30_z90`) ≈ 0.15–0.35; comfortably clears the Critic's redundancy threshold. No IC carve-out needed.
- **Expected importance rank**: 8–14 of 49 (mid-to-lower). It is a regime/crowding CONDITIONER, not a primary directional driver. Do NOT expect rank 1–3. If it lands rank 1–3, treat that as suspicious (sign-features rarely dominate gain) and check per-month stability before trusting it.

### 2. Do NOT stack a second OI variant this iteration
- Single-axis isolation. /083 already gave us two OI-family importance reads; one re-aimed sign-divergence feature on a fresh symbol is the clean test. Stacking `oi_delta_5_z30` short-window companion onto CRV at the same time would confound the divergence-feature verdict with a window-stacking effect (the same trap memorialized in `feedback_v3_engineered_features_dont_stack`). Hold it for /085 if /084 is PROMISING.

## Saturation Risks to Flag

1. **The R-FADE gate is the highest-variance element, not the feature.** R-FADE is a post-aggregator stateless VETO: it kills a trade when the model's sign opposes `oi_price_divergence_30` AND `|divergence| > 2.0`. Two failure modes the QR must pre-register a falsifier for: (a) **near-zero fire rate** — at z>2.0 on a sign-quantized {−2,0,+2} base, the z-score tail past 2σ may be very thin; if R-FADE fires on <3% of candidate entries it is INERT and the iteration collapses to a pure feature test (still valid, but relabel honestly as PROMISING-FEATURE not PROMISING-RISK). (b) **trade-rate floor breach** — the v1 per-specialist OOS floor is ≥50 (`feedback_v1_trade_rate_floor_50_per_specialist`). A VETO gate only REMOVES trades. CRV at single-symbol must clear 50 OOS trades AFTER R-FADE veto. Pre-register the expected veto count from IS calibration; if IS veto rate × OOS candidate count would drop OOS below ~60, the gate is too aggressive at z=2.0.

2. **CRV's +0.069 trivial baseline is barely-positive, not negative.** The directive's strongest precedents (DOT/063, AAVE/078) had genuinely NEGATIVE pre-rescue baselines. CRV's min-horizon is +0.069 — MEDIUM headroom, not HIGH. The real headroom is regime-localized (bear −0.924), which means the ML edge, if it materializes, will be concentrated in bear-regime months. Expect IS Sharpe to be carried by a minority of training windows; watch for high monthly-Sharpe dispersion (EDA already shows monthly std 3.567 — very high). This dispersion is the edge source AND the overfit risk simultaneously.

3. **Hot-vol regime weighting.** NATR p50 7.885% means CRV's loss surface is dominated by high-vol bars. The triple-barrier labels at ATR 2.9/1.45 will fire faster (wider absolute barriers), shifting the timeout/SL/TP mix vs the cooler bundle symbols. Not a defect — but the per-month label balance may skew, and class balance is what `class_weight` would address if it drifts past ~70/30. Flag the IS label distribution in the post-mortem.

## What I Did NOT Recommend, and Why
- **No `num_leaves` / `max_depth` bump** despite CRV being single-symbol: the methodology lock is binding AND the 50-seed ensemble already absorbs the variance that a wider tree would chase. Breaking the lock here would also break comparability against the /063/064/065/078 specialist roster.
- **No `class_weight='balanced'`**: triple-barrier at symmetric ATR multipliers is ~balanced; introducing it now adds a confound to the feature/R-FADE verdict. Defer to a post-mortem trigger only if IS positive-class < 30%.
- **No additional OI feature, no XGBoost swap, no labeling change**: single-axis discipline. This iteration tests exactly two things (one feature + one risk gate) on one reformed-selection symbol. Keep it clean.

## Closing Note

**Confidence: MEDIUM.** The reformed selection is sound and CRV is the right pick from the pool, but +0.069 is MEDIUM (not HIGH) headroom and the edge is bear-regime-localized — this will be a dispersion-heavy iteration. The single most important thing the QR must NOT ignore: **pre-register the R-FADE fire rate and the post-veto OOS trade count from IS calibration.** A VETO-only gate that either never fires (INERT) or fires enough to breach the ≥50 OOS floor is the dominant failure path here — bigger than the feature itself. Predicted CRV specialist IS Sharpe: **+0.55** (range +0.30 to +0.80; bounded below DOT/063's +1.32 because CRV's headroom is regime-narrow, and bounded above the FIL/083 −0.82 disaster because the trivial baseline is no longer dominant). If R-FADE is INERT, the feature alone likely lands IS ~+0.45.
