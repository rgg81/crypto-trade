# LightGBM Master Advisor — iter-v1/013 — Phase 4.5 (Pre-Design)

## Context Read

- **Track**: v1. Branch `iteration-v1/013`. HEAD `c18e734`.
- **Baseline**: `v0.v1-baseline-corrected` (commit `f8bc12c`). IS +0.2829 / OOS +0.6637. Unchanged post-/010/011/012.
- **Brief**: cycle-2 EXPLORATION #8 of 10. Single axis variation: `--ensemble-seeds-offset 6` (window `[3003, 4004, 5005]`). R5-BINARY-KILL BIT-IDENTICAL to /011 + /012.
- **My track record**: 0/10 directional + 4 PARTIAL. /012 Phase 4.5 P50 was A SUBSTRATE-LOCKED at 65%; observed C PARTIAL at F7=32.71%. REFUTED.
- **2-property decomposition** committed at /012 Phase 7.4 — /013 is the 4th data point validation.

## 1. Substrate Decomposition Prediction

Held at HIGH confidence: **F9 PASS at ~80% probability**. The substrate-magnitude trajectory +0.4701 → +0.4849 → +0.5167 has std=0.025 across 3 mechanistically distinct conditions. Drift is monotonic-positive — consistent with TPE finding marginally better basin at successive seed windows OR a 3-point trend artifact. /013 P50 IS Δ ≈ **+0.52**, slightly above the [+0.38, +0.58] band midpoint to honor the drift. If F9 lands within [+0.38, +0.58], 4/4 substrate-magnitude lock VALIDATED — the decomposition becomes a permanent v1 axiom per brief Section 12.

The +0.52 P50 is NOT a strong upward bias — it's the natural extrapolation of `regress(IS_Δ ~ offset_index)` slope of ~+0.023 per offset step. /013 at offset=6 extrapolates to +0.516. I am **NOT** willing to predict the drift continues to +0.55 outside the band; my P50 stays at the upper-band region but the band is honored.

**Catastrophic-undershoot risk (F9 < +0.38)**: ~12%. Mechanism: a basin draw at `[3003, 4004, 5005]` could land in a non-LTC-dominant minimum, returning Sharpe-Δ closer to the BASELINE-mechanical layer (~+0.10). This is the "true B SEED-LOCKED" outcome that /012 didn't materialize.

## 2. R5-BINARY-KILL CONFIRMATION at /015 — Honest Read

**P(F1 OOS Δ > +0.05) at FLAT prior = 60-65%.** Decomposition:

- Outcome A (substrate-locked roster + positive OOS) — ~30% × ~0.70 conditional positive = **21%**
- Outcome B (seed-locked, surprising positive OOS) — ~30% × ~0.30 conditional positive = **9%**
- Outcome C (partial roster + positive OOS) — ~40% × ~0.75 conditional positive = **30%**
- Total: **~60%**

Per Section 5 prior. Slight upward adjustment to 65% because /011 + /012 are both well above the +0.05 threshold (+0.41 and +0.27 are not boundary cases) — the OOS-amplification fraction has empirical floor around +0.20 even in worst observed case, and the +0.05 threshold is below this floor. **Most likely outcome: /015 = R5-BINARY-KILL CONFIRMATION.**

But — and this is load-bearing — the **/015 CONFIRMATION will likely DISSOLVE the basin lottery**. Per my /012 Phase 7.4 §1: the mechanical kill_low layer is ~+0.05 OOS Δ at multi-seed. The /011's +0.41 and /012's +0.27 are basin-lottery-AMPLIFIED single-seed observations. The 10-seed CONFIRMATION OOS Δ will not be +0.30 — it will be closer to +0.05-+0.15. If QR / Critic interprets a /015 multi-seed OOS Δ of +0.08 as "confirming the +0.30 EXPLORATION signal" that would be the wrong frame. The CONFIRMATION measures the MECHANICAL layer, not the basin-lottery amplification.

## 3. Risks to Flag at Critic Phase 7.5

Specific patterns from /011 + /012:

- **Per-symbol catastrophic reversal**: /011 BTC modest; /012 DOT = **-179.84** (raw PnL collapse). Pattern: ONE non-LTC symbol becomes catastrophic per seed window. /013 may produce a third symbol catastrophic-reversed (LINK at +105.86 in /012 is the next candidate). Critic should attend per-symbol raw net PnL std across /011/012/013, NOT pct_of_total_pnl.
- **Denominator effect on `pct_of_total_pnl`**: /012 total IS PnL was small (~+28.85 vs /011's +103.85), inflating LTC pct to 412.12% (LTC raw was +118.92, only +7.5% above /011's +110.58). If /013's portfolio total IS PnL collapses to single digits, LTC pct could exceed 1000% — pure denominator artifact.
- **F1 boundary at +0.05**: brief Section 8.1 row partition at exactly +0.05. If /013 OOS Δ lands at +0.04-+0.06, the pre-committed /015 axis selection routes on a boundary value. Recommend Critic pre-attend: if F1 ∈ (+0.03, +0.07), declare F1 numerical-fuzzy and require seed-determinism audit at /013 closeout BEFORE the /015 axis is finalized.
- **F7+F8 boundary edges**: /012's F7=32.71% was 2.71pp from the 30% threshold. Single-percentage-point misses should NOT be treated as decomposition refutation.

## 4. Honest Confidence — What I'm Willing vs Not Willing to Predict

**WILLING (HIGH confidence)**:
- F2 R5 fire rate ∈ [16%, 24%] both IS and OOS
- F9 PASS at ~80% probability (substrate-magnitude lock)
- F1 OOS Δ ≥ +0.05 at ~60-65% probability

**WILLING (MEDIUM confidence)**:
- LTC remains rank-1 dominant IS symbol
- LINK or DOT or BTC produces another per-seed catastrophic-reversal

**NOT WILLING**:
- Specific F1 OOS Δ magnitude (range +0.05 to +0.55 plausible; magnitude track record poor)
- Which specific symbol catastrophically reverses
- F7 vs F8 magnitude ordering (whether F7 < F8 or vice versa)
- Whether OOS-amplification fraction lands in [+0.45, +0.78] band as observed at /011/012

## 5. /014 Pre-Stage Recommendations Conditional on /013 Outcome

- **/013 IS Δ in [+0.38, +0.58] AND F1 > +0.05** (decomposition VALIDATED + R5 positive) → **/014 = UNUSED-family EXPLORATION (labeling)**. The R5-BINARY-KILL CONFIRMATION is pre-committed for /015 — /014 should NOT be another R5 EXPLORATION. Use /014 to seed the /015+ UNUSED-family CONFIRMATION pipeline. Specifically: **triple-barrier σ_t source via past-only EWMA at 14-day window** (brief Section 11 Alternate A; HIGH-RISK declaration).

- **/013 IS Δ outside [+0.38, +0.58]** (substrate decomposition REFUTED) → **/014 = methodology-substrate-test offset=9 OR halt-and-reassess**. If F9 fails, the decomposition is wrong and we don't yet know what the correct framing is. /014 = 4th seed-window sample to bound the variance properly.

- **/013 F1 ≤ 0** (R5 OOS negative — 2/3 positive) → **/014 = UNUSED-family EXPLORATION (labeling at triple-barrier σ_t source)** per pre-committed /015 = UNUSED-family CONFIRMATION. /014 = the EXPLORATION precursor to the labeling CONFIRMATION; produces the 1 prior EXPLORATION required by cadence discipline to legitimize the /015 labeling CONFIRMATION. **HIGH-RISK declaration mandatory** for /014 in this branch.

## Closing Note

**Single non-ignorable point**: the /015 multi-seed CONFIRMATION will dissolve the basin lottery to ~+0.05-+0.15 OOS Δ regardless of what /013 shows. The pre-committed conditional ("F1 > +0.05 → R5 CONFIRMATION") is mechanically correct but the QR / Critic must NOT interpret a /015 multi-seed Δ of +0.08 as "weaker than expected." The single-seed +0.41 and +0.27 are amplifications, not edge estimates. My /012 §1 framing on this is what /015 will test, and the test is decision-critical for whether R5-BINARY-KILL becomes the first v1 ingredient to update BASELINE_V1.md.

**Track record discipline**: 0/10 directional + 4 PARTIAL. Magnitude predictions (substrate-anchored) earn HIGH confidence; verdict-class predictions (FLAT prior) earn nothing more than the priors. /013 Phase 7.4 will test whether my substrate-magnitude lock claim survives a 4th data point — that is the only credibility-stake I am willing to bet on.

No hyperparameter or feature changes recommended. Brief Section 3 axis isolation is mechanically clean. The substrate-test axis is the right experiment to run.
