# LightGBM Master Advisor — iter-v1/085 — Phase 4.5 (Pre-Design)

## Context Read
- Track: v1. Baseline: BUNDLE-002 (`v0.v1-082`), DOT/063 + ETH/064 + BTC/065 + AAVE/078, IS +0.72 / OOS +1.00; pairwise-disjoint universe {BTC, ETH, DOT, AAVE}.
- Prior iter /084 outcome: SPECIALIST-NEGATIVE catastrophic (CRV IS −2.47); fresh-mine 0/4 (ATOM/ICP/FIL/CRV). The /084 post-mortem established GATE 2 (probe IS Sharpe ≥ +0.30 AND max feature-vs-label |IC| ≥ 0.04 AND autocorr ≥ 0.03) — the structure pre-screen CRV would have failed.
- QR Phase 4 output (read directly): `analysis/iteration_v1-085/uni_prescreen_results.csv`, `probe_UNIUSDT_results.csv`, `structure_prescreen_summary.csv`. UNI structure-profile = volatility-regime / 3-bar (lag-3 NEGATIVE) mean-reversion; directional-momentum ICs dead.
- User directive 2026-06-09: multi-seed CONFIRMATION PERMANENTLY DROPPED; KEEP MINING with the /084 structure-gate lesson; ONE coin (UNI), NEW feature-engineering SET starting at 4, grind toward 10. Methodology LOCKED: 50 seeds × 30 trials × specialist_mode × LightGBM × max_depth=5 × num_leaves=31. "4→10" is the FEATURE-SET size, not seeds/trials.
- Code state: `V1_ITER085_FEATURE_COLUMNS` (LOCAL, 52 = PRUNED 48 + 4 new) already scaffolded; global `V1_FEATURE_COLUMNS_PRUNED` UNCHANGED (the /084 PRUNED-stays-48 invariant holds); `V1_ITER085_UNIVERSE = ("UNIUSDT",)`; UNI ∉ V1_EXCLUDED_SYMBOLS; UNI ∉ {DOT, ETH, BTC, AAVE} (pairwise-disjoint PASS).

## CRITICAL — Gate Status Is GATE 1 PASS / GATE 2 MARGINAL-FAIL (read the numbers, not the prose)

I will not soften this, because /084 cost the campaign its worst-ever IS (−2.47) by under-weighting exactly this signal. The measured probe data for UNI on the 48-col PRUNED stack:

- **GATE 1 PASS**: trivial-momentum min-horizon baseline = **−0.2485** (most-negative in the eligible pool; naive momentum whipsaws on UNI — confirms it is NOT a FIL-type clean-trend trap). Clean pass of ≤ +0.15.
- **GATE 2 PRIMARY — FAIL**: probe IS monthly Sharpe = **−0.243** (`probe_UNIUSDT_results.csv`, `gate2_pass=False`). The /084-established threshold is ≥ +0.30. UNI is **0.54 Sharpe below the gate** and sits in NEGATIVE territory — directionally the same region CRV occupied.
- **GATE 2 SECONDARY — MARGINAL FAIL**: max feature-vs-label |IC| = **0.0393** (vol_bb_bandwidth 0.0393, natr_30 0.0386) vs threshold ≥ 0.04. Off by 0.0007 — a hair under, on volatility-STATE features only; every directional IC is dead (ret_5d −0.0026, ret_21d +0.0092, rsi_14 +0.0021).
- **GATE 2 TERTIARY — PASS (and it is the one genuinely encouraging number)**: autocorr_mag = **0.0843**, the strongest in the pool, driven by lag-3 = **−0.0843** (lag-1 −0.026, lag-7 +0.0164). This is a real, measured 3-bar (~1 day) mean-reversion signature — NOT noise-of-zero like CRV (whose lags were all within ±0.026 of zero). `structure_signal=WEAK`.

**The honest reconciliation**: the directive's "GATE 1 + GATE 2 passed" framing is not what the CSVs say. The probe FAILED on the OLD 48-col stack. The legitimate thesis for proceeding — and it IS legitimate — is that **the probe failed because the PRUNED stack has no coordinate for UNI's structure**: it carries lag-5 autocorr (not lag-3), and vol_natr_14 (not the natr_30 window where UNI's vol IC concentrates). The 4 new features are precisely the missing coordinates. So this is NOT the CRV case (CRV had NO structure at any coordinate — autocorr near-zero, diffuse importance). UNI has WEAK-but-real structure that the current stack cannot see. That distinction is the entire bet. It is defensible, but it is a bet on feature engineering rescuing a sub-gate probe — categorically higher-risk than DOT/063 or AAVE/078, which cleared structure on the stock stack.

## Recommended Hyperparameter Direction

### 1. KEEP methodology fully LOCKED — do NOT touch num_leaves / max_depth / trials / seeds
- **What**: 50 inner seeds × 30 trials × `max_depth=5` × `num_leaves=31`, specialist_mode, exactly as the lock specifies. No deviation.
- **Why**: this is a single-axis FEATURE-SET iteration. The only variable under test is the 4-feature reversion set. Any HP change confounds the feature verdict. `num_leaves=31` is at the soft cap `2^5−1` for depth 5 — already correctly matched; no headroom to widen without raising depth, which the lock forbids.
- **Expected effect**: none (held constant by design).
- **Risk**: none from holding; the risk lives entirely in the feature set and the sub-gate probe.

### 2. Raise `min_data_in_leaf` floor in the Optuna search (the ONE HP lever that fights the 4-feature overfit)
- **What**: if the runner exposes `min_data_in_leaf` (a.k.a. `min_child_samples`) in the Optuna space, set its LOWER bound no lower than ~80–100 for this UNI cell (vs the more permissive ~20 default). Do NOT change depth/leaves.
- **Why**: 52 features on a single ~4.5y / ~3300-bar IS window, with the 4 new features explicitly built to carry the signal, is a fertile overfit surface — and a sub-gate probe means the IS loss surface is shallow, so Optuna at 30 trials can chase noise into thin leaves. A higher leaf floor regularizes against fitting 3-bar-reversion noise into sparse leaves. This is regularization the lock permits (it is not depth/leaves/trials/seeds).
- **Expected effect**: marginal IS Sharpe DAMPENING (−0.05 to −0.15) in exchange for materially better IS→OOS transfer. On a marginal-structure symbol, transfer is the whole game.
- **Risk**: too high a floor (>300) starves the 3-bar reversion signal that lives in a minority of bars; keep it ≤ ~100. If the runner does NOT expose this knob, do not add it (no src changes mandated here) — note it as the first lever to reach for in /086 if /085 lands IS-positive-but-overfit.

### 3. Confirm `lambda_l1 > 0` is reachable in the Optuna space
- **What**: ensure `lambda_l1 ∈ [0, ~5]` is searchable (it is in the standard v1 space). Do not pin it.
- **Why**: 52 features with high intra-stack redundancy + 4 deliberately-correlated reversion features (rev_vol_gate_signed is a composed capstone binding the other 3) → L1 sparsity lets Optuna prune toward a stable subset rather than spreading split budget across redundant axes (the diffuse-importance fingerprint that doomed CRV). On a reversion symbol you WANT the model to concentrate on the 2–3 reversion coordinates, not smear.
- **Expected effect**: cleaner, more concentrated feature importance; modest IS effect, better stability.
- **Risk**: none — it is already in the search space; this is a "verify, don't change" item.

## Recommended Feature-Engineering Direction

The 4-feature set is well-constructed and I endorse its SHAPE — it is the diametric opposite of both /083 FIL (no momentum features here — correct, UNI's momentum is dead) and /084 CRV (every feature is anchored to a SPECIFIC measured UNI coordinate, not narrative). My job is to predict where each lands and pre-register the falsifiers.

### Set: rev_extension_z_3 / vol_state_z_natr_30 / rev_halflife_50 / rev_vol_gate_signed
- **What**: an orthogonal signal / state / speed / interaction decomposition of UNI's reversion-in-vol-regime profile. rev_extension_z_3 = the lag-3-NEGATIVE overextension (sign-flipped, high = expect-bounce) = the direction; vol_state_z_natr_30 = the regime-STATE conditioner; rev_halflife_50 = reversion speed (a genuinely new kernel — no reversion-speed feature exists anywhere in v1); rev_vol_gate_signed = the composed capstone (signal × state), the inverse of the proven regime_momentum_signed_5d pattern.
- **Pre-registered IMPORTANCE predictions** (HARD falsifiers, learned from /084 where I under-weighted my own flags):
  - **rev_extension_z_3 — predict rank 1–4.** This is UNI's strongest measured structure (autocorr_mag 0.0843) and the coordinate the PRUNED stack MISSES (it carries lag-5 not lag-3). If it lands rank 1–4 with CONCENTRATED gain → real signal, the bet is paying. If it lands rank 14+/52 INERT → the 3-bar reversion does not survive the triple-barrier label transform → this is the leading single indicator the iteration will fail. **This feature's importance IS the experiment.**
  - **vol_state_z_natr_30 — predict rank 3–8.** Regime conditioner; UNI's only near-gate vol cluster. Utility, not primary.
  - **rev_halflife_50 — predict rank 6–12, HIGH instability (std-of-rank > 3 expected).** Half-life kernels are noisy on 8h bars; I expect it to bounce. Flag for /086 reconsideration if std-of-rank > 4.
  - **rev_vol_gate_signed — predict rank 2–6 IF the other three are real; rank 1 = SUSPICIOUS.** A composed capstone landing rank 1 with the primitives INERT is the /084 fingerprint in a new coat (high gain on a feature the model leans on because it has nothing else). **If rev_vol_gate_signed is rank 1 AND rev_extension_z_3 is rank 8+, treat as anti-signal, NOT as confirmation.**
- **IC pre-warning**: rev_vol_gate_signed is a composed feature (signal × state) and will mechanically correlate with its primitives — expect high |IC| with rev_extension_z_3. This is the Category-2 carve-out (`feedback_v3_engineered_feature_pivot`): do NOT let a |IC|>0.50 between capstone and primitive be read as a redundancy failure. The Critic's feature-vs-LABEL IC (Check 4) is the relevant test, not feature-vs-feature.

## Saturation / Marginality Risks to Flag

**Risk A — the probe is sub-gate and the bet is that 4 NEW features flip it.** This is the dominant risk and it has NO precedent in the v1 win column. Every v1 specialist that worked (DOT, ETH, BTC, AAVE) cleared structure on the STOCK stack; UNI is the first attempt to manufacture a pass via feature engineering on a coin the probe rejected. The /084 post-mortem's burden-of-proof note applies in full force: "negative-baseline AND structure-present → positive specialist is UNTESTED" — and here we don't even have structure-present on the existing stack, we have structure-present-only-at-uncarried-coordinates. The thesis is coherent (UNI ≠ CRV: real lag-3 reversion vs zero autocorr) but it is a conjecture, not a demonstrated pattern.

**Risk B — 4 features on one ~3300-bar IS window at 30 trials × 50 seeds.** The 50-seed inner ensemble is the variance reducer that should prevent a CRV-style single-path blow-up (CRV's −2.47 was at the same 50-seed lock, so seeds alone are NOT a guarantee). The realistic failure mode here is NOT a −2.47 crater (UNI has real reversion structure and the features are vol-anchored, so confidently-wrong-at-max-vol is less likely than CRV) but a quiet IS-positive / OOS-negative split — the model fits IS reversion timing that drifts OOS. Watch the IS/OOS Sharpe ratio at post-mortem; a ratio < 0.4 is the tell.

**Risk C — the ≥50 OOS trade floor.** UNI is a reversion model fading short-horizon extension; reversion entries on 8h bars over the OOS window may be sparse. Pre-register the expected OOS trade count from IS calibration. If the reversion gate (rev_vol_gate_signed) is selective, OOS trades could fall below the 50-per-specialist floor (`feedback_v1_trade_rate_floor_50_per_specialist`) → auto-downgrade. This is a real and under-discussed path to a non-mergeable result even if Sharpe is fine.

## What I Did NOT Recommend, and Why

- **I did NOT recommend re-running the probe with the new 52-col stack before the full specialist** — though I would have, if the lock allowed. The cheapest de-risking move is a single-seed n_trials=10 probe on the 52-col stack: if THAT still prints negative, the feature engineering did not flip the structure and the full 50-seed run is a known-loss. I flag this as the single highest-value optional pre-flight, but I do not mandate it (QR's call; it adds minutes, not hours).
- **I did NOT recommend starting at fewer than 4 or jumping to 10 features now.** 4 is correct: the signal/state/speed/interaction quadrants are claimed, and /086 adds the 6 named extensions (bb_pctb_20 distance-to-band, range-spike reversion trigger, BTC-vol-regime gate, lag-3-vs-lag-7 sign confirmer, overshoot-magnitude, reversion-failure detector) WITHOUT redundancy. Grinding from 4 is the right cadence.
- **I did NOT recommend any momentum-shaped feature.** UNI's momentum is dead (all directional ICs within noise of zero); a momentum feature would re-make the FIL trap in reverse. The set is correctly momentum-free.
- **I did NOT recommend class_weight / objective changes, XGBoost swap, or labeling changes.** Single-axis discipline; the lock forbids it and it would confound the feature verdict.

## Closing Note

**Confidence: LOW-to-MEDIUM (lean LOW).** I am giving this LOW honestly because the load-bearing gate — the probe — is NEGATIVE (−0.243), and I was burned at /084 for treating a borderline structure signal as headroom. What pulls it OFF the floor toward MEDIUM is genuine: UNI is demonstrably NOT the CRV case (real lag-3 reversion at autocorr_mag 0.0843 vs CRV's flat-zero, and a coherent reason the probe failed — the PRUNED stack literally lacks the lag-3 and natr_30 coordinates). The feature set is the best-targeted I have reviewed in the mining campaign. But "best-targeted feature set on a coin whose probe failed" is still a conjecture the v1 win column has never validated.

The single most important thing the QR must NOT ignore: **pre-register rev_extension_z_3's importance rank as a HARD falsifier BEFORE the run, and pre-register the expected OOS trade count.** If rev_extension_z_3 lands INERT (rank 14+/52), the 3-bar reversion did not survive the label and the iteration has failed regardless of the headline Sharpe — that is the /084 lesson made concrete. And if the capstone rev_vol_gate_signed dominates while the primitives go quiet, that is the anti-signal pattern, not a win.

**Predicted UNI specialist IS Sharpe: +0.35** (range **+0.10 to +0.65**). Bounded BELOW by the negative probe (−0.243 on the old stack means the new features must add ~+0.6 of IS Sharpe just to reach the gate, which is plausible-but-unproven for 4 targeted reversion coordinates), and bounded ABOVE well short of DOT/063's +1.32 because UNI's structure is WEAK (autocorr_mag 0.0843, |IC| 0.0393 — an order of magnitude thinner than a strong-structure coin). If the 4 features are INERT or near-INERT, the specialist lands at roughly the probe (~−0.10 to −0.25), and the correct verdict is SPECIALIST-NEGATIVE with the diary lesson "feature engineering could not manufacture a structure-gate pass on a sub-probe coin."

---

## Phase 7.4 — LightGBM Master Post-Mortem (iter-v1/085)

**Confidence in this read: HIGH.** 50-seed cross-seed Sharpe std = 0.000 → the negative is structural, not sampling noise. Phase 4.5 modal (+0.35) missed by ~1.05 Sharpe; the miss is owned below.

**Outcome:** IS Sharpe −0.7005 (168 trades, WR 38.1%, PF 0.81, MaxDD 91.36%); OOS +0.1739 (84 trades, PF 1.05, MaxDD 21.42%); ratio −0.2482. Triple-falsified SPECIALIST-NEGATIVE (F2-PRIMARY + F3 + F4).

### 1. Feature-binding triage
- **Vol-state bound as redundancy, not signal.** vol_state_z_natr_30 (rank 3, gain 5919.8) + rev_halflife_50 (rank 9, 3582.8) paraphrase the incumbent vol stack: vol_atr_14 (rank 1, 13069.9), vol_natr_14 (rank 12, 2857.9). Split-budget redistribution within the vol-state family (feedback_v3_promising_feature_mechanical fingerprint), NOT orthogonal gain.
- **Direction inert via LABELING-HORIZON MISMATCH (the load-bearing finding).** rev_extension_z_3 (rank 42, gain 203.5) is a 3-bar return-extension; the triple-barrier label fires on 2.9×/1.45× ATR excursions. A 3-bar reversion (sub-1% on an 8h bar) completes INSIDE the 1.45×ATR stop distance → the label never sees a distinct outcome. Corroborated: inherited interact_ret1_x_ret3 (rank 49) — the closest lag-3 proxy — is ALSO near-dead. No lag-3 encoding survives THIS label. rev_vol_gate_signed (rank 39) inherits the primitive's deadness by construction. F2-SUSPICION correctly did NOT fire — clean signal-absence, not the /084 anti-signal pattern.

### 2. Phase 4.5 prediction vs reality — owned
- **Defensible:** LOW confidence was earned (probe −0.243, no v1-win precedent for rescuing a sub-probe coin); failed in the exact Section-7 modal direction (NEGATIVE-PROBE-FLAT).
- **Genuine error (key lesson):** conflated autocorr_mag 0.0843 in RAW RETURNS with learnable label causation under the triple-barrier transform. "Real in raw returns" ≠ "extractable through an ATR-barrier directional label." The GATE-2 probe (runs the real label) said −0.243 and was RIGHT; the return-space autocorr argument was the blind one. **Hardwired for /086: screen a raw-return autocorr/IC signal against the actual label horizon + magnitude, not just in return-space.**
- Predicted −0.05/−0.15 dampening; actual −0.46 below probe (inert features × 30-trial Optuna = amplified overfit surface, feedback_v3_inert_features_at_higher_budget).

### 3. Optuna read (2298 studies parsed)
best-trial IS-objective mean +0.116 (std 0.108) vs walk-forward IS −0.70 → structural overfit gap. reg_alpha std 2.43 (full-range), training_days std 170 (full-range), n_estimators std 127 — search wandering a flat/noisy loss surface with no informative gradient. best−runnerup gap 0.020 → NOT curve-fit-to-one-trial. cross_seed std 0.000 → all 50 seeds robustly converged to the same bad answer; no profitable basin exists.

### 4. Catastrophe mechanic (under-weighted by the headline)
monthly_pnl: 15 pos / 15 neg IS months (coin-flip). **2022-09 alone = −43.87% of the −46.63% IS total (94% of all loss).** trades.csv 2022-09: 7/8 stopped out, ~all at weight_factor≈1.0 because R5's 45-day vol-target history hadn't accumulated at IS-start → full-size capital into UNI's listing-shock with no vol damp (all-IS mean weight_factor 0.401). IS-ex-2022-09 ≈ −2.8%. The TRUE signal verdict is "structureless coin-flip"; the −0.70/91%-MaxDD magnitude is an R5 cold-start amplifier. Still clearly NEGATIVE (38% WR across all 168 trades), but the magnitude shouldn't be over-attributed to the features.

### 5. Next-iter implications (advisory)
- **5a (PRIMARY): make GATE-2 PRIMARY probe (≥+0.30 on the REAL label) a HARD REJECT, not a soft "feature-engineering can flip it" flag.** All v1 wins (DOT +1.32, ETH, BTC, AAVE) cleared structure on the stock label-probe; zero wins ever came from rescuing a probe-reject. CRV + UNI = two consecutive correct GATE-2 predictions. Close the "manufacture a pass via features" hypothesis.
- **5b (optional, technically-correct confirmation): a short-horizon fixed-bar reversion label** (sign of 3-bar-forward return, or ±k-bp barrier at reversion magnitude not 1.45×ATR) would put the label on the kernel's time-scale. Run as an ISOLATED labeling EXPLORATION on an ALREADY-STRUCTURED coin FIRST (validate the label before applying to a sub-probe coin). Lean 5a primary; 5b only to confirm the kernel is unreachable rather than merely unreached.
- **5c: do NOT carry the 4 features forward.** Directional pair (rank 39/42) confirmed INERT + IS-harmful; drop both. Vol-state pair (rank 3/9) redundant with vol_atr_14/vol_natr_14; drop for cleanliness unless a future coin's screen flags natr_30 specifically.
- **5d: R5 cold-start hazard (systemic)** — vol-target runs near 1.0 in the first ~45 IS days exactly when a new/volatile coin is riskiest; systemic NEGATIVE amplifier, not UNI-specific.

### Notes for Critic (7.5)
1. Check-8: the +0.17 OOS is coin-flip noise on a structureless model (15/15 IS split), NOT a regime-specialist signal — don't let it soften the NEGATIVE.
2. The −0.70/91%-MaxDD is 94%-driven by 2022-09 R5 cold-start; signal verdict is milder than the magnitude but still NEGATIVE.
3. If /086 retains these 4 columns, that's a Check-worthy regression (inert-and-harmful).
