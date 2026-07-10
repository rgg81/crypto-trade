# REVIEW-A2-preflight — Critic Pre-Flight of the EXPLORATION-A2 Brief (MN track)

**Reviewer:** Quant Critic (Fable, read-only). **Date:** 2026-07-10. **Persisted by orchestrator.**
**Contract under review:** briefs-portfolio-mn/EXPLORATION-A2.md (85bbe30f) — the axis-1
successor the Critic's own REVIEW-A recommended. Quarantines honored; holdout sealed; no runs.

## VERDICT: **PASS-WITH-CONDITIONS** — C1–C4, ALL additive reporting/instrumentation; none
re-opens the frozen construction, gates, predictions, or decision map. No brief re-freeze
required; the QE folds them into the required tables.

## Per-check rulings
1. **ONE-change isolation: CLEAN.** Byte-frozen signal/universe/floor/cap/cadence/ensemble;
   sole change = HedgeOverlay → in-weight projection. Variant reduction correct (Cell-3 is the
   revealed no-neutralization reference — cited, not re-run). The §4 relabel text does not
   weaken any gate. Sign-flips are a property of the method, instrumented by ρ(w_proj,w_raw).
2. **Projection math VERIFIED correct/complete.** Orthogonal projection onto null(A) zeroes
   both constraints exactly; scalar rescale preserves both; cap-last breaks Σw·β=0 by a
   MEASURED residual (post_cap_target_beta reported, not asserted) — post-cap re-projection
   correctly NOT required (alternating-projection non-convergence; the realized-β gates are the
   arbiter). Genuine trouble spot: the collapse-guard fires only below 0.10·gross; the
   0.10–0.5·gross zone rescale-amplifies 2–10×, clipping to near-uniform-at-cap in exactly the
   high-|β| 2024-25 era → **C1: report pre-rescale Σ|w_proj| distribution + max amplification;
   flag rebals >2×.**
3. **G3 disclosure honest on mechanism, optimistic on point estimate.** With Σw_target ≡ 0 at
   every rebal, the only |Σw| source is mid-hold force-exits — Cell-3's revealed 0.1080 > 0.10
   via the SAME mechanism A2 inherits. **The modal outcome is FAIL-G3-at-force-exit-floor**, not
   the edge case the 0.10 point implies (band [0.05,0.15] covers it; precedent named). Decision
   map handles it correctly (p=0 forensic + passing realized β → Sharpe answer + user-gated
   unseen-data G3-re-spec CONSIDERATION). → **C2: verify the p=0 decomposition runs; frame to
   the user that SUCCESS→reveal is the LESS-likely branch.**
4. **Both-ways thresholds (≥1.30 intact / ≤0.70 disguised) principled, not gamed.** Anchoring
   to revealed Cell-1 is the experiment. The QR band excluding collapse is EVIDENCE-based:
   Cell-1 (+1.7753 hedged) ≈ Cell-3 (+1.7195 unhedged) → the hedge leg carried ~no return; the
   alt book's β is NEGATIVE (a drag over an up-drifting IS) → "disguised beta carried the edge"
   is genuinely unlikely. → **C4: also report A2/Cell-3 ratio + delta (the sharper comparator).**
5. **BTC-only projection + measured ETH: coherent** ("neutralize what you estimate well,
   measure the rest"); evidence- and conditioning-grounded. A2-ETH one-shot contingency tightly
   bounded (sole-ETH-failure trigger, cond-guard fallback with flag, +1 n_eff, terminal).
6. **Contingency audit: within /006-007 discipline, NOT a hydra.** The two contingencies are
   MUTUALLY EXCLUSIVE by construction (one needs G1b fail, the other needs G1/G2 pass) → at
   most one fires; clean terminal FAILs exist with no escape (edge-collapse, other-HARD).
   Standing note: at ~9 DOF post-contingency this is the family's LAST bounded retry before
   SUCCESS→reveal or terminal shelf.
7. **Ledger 7→8(→9) honest. Warmup catch verified sharp:** dropping β_eth_resid does NOT
   shorten the warmup — the universe ≥270-candle history filter binds → same k=273 / mask 293;
   A2 scored on the IDENTICAL 293 mask (candle-for-candle comparability). beta_neutralize test
   spec thorough (inert byte-identity, corrupt-future-β control, projection-correctness ≤1e-12,
   minimal-distortion row-space check, degenerate/collapse guards, cap-ordering honesty).
   Ground-truth 2× retained per the new catalog rule; analytic twin valid again (stateless) as
   cross-check. → **C3: decompose realized rolling β_BTC into projection-target + cap-residual
   + estimation contributions (the thin-G1a adjudication; Cell-1 passed G1a at only 96.0%).**

## Conditions
C1 pre-rescale distribution + amplification flags · C2 p=0 forensic verified + modal-outcome
framing · C3 rolling-β decomposition in the neutrality panel · C4 A2-vs-Cell-3 comparison.

## Why not BLOCK
No leak, no hidden change, no math error, no gamed threshold, no unbounded escape, no seal risk.
The conditions make the likely FAIL-G3-floor and possible thin-G1a outcomes adjudicable rather
than silent.
