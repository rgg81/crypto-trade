# CRITIC PRE-FLIGHT RULING — EXPLORATION-S4 (MN3 track)

> Persisted VERBATIM by the orchestrator from the Critic's read-only pre-flight, 2026-07-11.
> Verdict PASS-WITH-CONDITIONS; C1–C4 applied via EXPLORATION-S4-AMENDMENT-001 (appended to the brief) before the scored run; C5–C6 carried into the run instructions.

**Verdict: PASS-WITH-CONDITIONS** (2 MUST-fix pre-run + 2 SHOULD + 2 recommendations; none re-opens the construction, the signal, the gate anchoring, or the throttle Layer-2 legitimacy).

**Model disclosure (charter deviation).** This ruling was authored on **Opus 4.8, not Fable** — the Fable mandate is user-suspended this phase (Fable-5 rate limit; "continue on Opus"). The brief under review was likewise authored on Opus (disclosed in its MODEL-NOTE). Adversarial burden and standard are unchanged; nothing has been revealed; the holdout is sealed; `MN3-H` is unspent (verified against `REVEAL-LEDGER.md` — zero spends).

**Object reviewed:** `briefs-portfolio-mn3/EXPLORATION-S4.md`. **Governance cross-read:** `ORCHESTRATOR_BRIEF_MN3.md`, `DIAG-H.md`, `PLAN.md` §3.2/§6.1 + AMENDMENT-002 §C/§D + AMENDMENT-003 §C, `CRISIS-FALSIFY-003.md` + `CRISIS-MACHINE-DISPOSITION.md` (the load-bearing floor-death record), v2 `EXPLORATION-A.md`/`A3.md`/`CONFIRMATION-A.md` (SCUD provenance + 11-HARD template), `REVEAL-LEDGER.md`.

The construction is sound and, on neutrality apparatus, materially **stronger** than the sanctioned v2 template (it adds a shuffled-signal placebo the A-family lacked). The gate anchoring survives the adversarial audit almost completely intact — decisively so, because most S4-specific realized numbers (Sharpe, maxDD, CS-A cost stress) **do not exist yet at pre-flight**, so "fitted to the realized value" is structurally impossible for them, and every threshold that *could* have been read off DIAG-H's revealed scorecard is instead the verbatim v2/charter value or a zero/sign floor. The defects I am conditioning on are **decision-map completeness holes** (an overlap and a gap that would force post-hoc discretion — the exact thing pre-registration forbids) plus one soft-anchored sample sub-floor. All are fixable by a dated `EXPLORATION-S4-AMENDMENT` before the scored run, at zero cost. That is why the verdict is conditions, not BLOCK.

---

## Checklist rulings

### 1. Gate anchoring — PASS (one soft sub-floor conditioned, C3)

The fittable surface is narrow: the only DIAG-H numbers the QR could read a threshold off are **+17%/yr, med +13.9%, 19/21 positive, H1/H2 +13.9/+19.5, CRASH +54.0 / MANIA +25.8 / CHOP +7.4, turnover 74×**. I checked every HARD threshold against that scorecard. Note DIAG-H reported **no Sharpe and no maxDD** at the sleeve level — so the two thresholds an adversary would most suspect (G-sharpe-floor, G-maxdd) had **no realized value on the scorecard to fit to**.

| HARD gate | Threshold | Anchor | Why it is NOT a fit to S4 |
|---|---|---|---|
| G1a / G1b | β_BTC ≤0.10@95%/max0.20; β_ETH ≤0.15@95%/max0.25 | charter PLAN §1.4 verbatim | Identical to v2 neutrality gate; not a function of any S4 number |
| G2-CRASH / G2-MANIA | \|β_BTC\| ≤0.15 each | charter G2, split | S4's +54% CRASH is a *return*, not a beta; the engine weight-projection β is an **unmeasured unknown** (R1) — flagged as a genuine discriminating risk, not pre-guaranteed |
| G3 | \|Σw\| ≤0.10·gross | charter verbatim | Structural neutrality bound |
| G4 | worst-bucket t > −1.0 | charter verbatim | A fixed principle bar; S4 clears it comfortably but the *threshold* is charter-set, not read off +54/+25.8/+7.4 |
| G-sharpe-floor | ≥ +0.35 | **v2 EXPLORATION-A verbatim** | +0.35 = economic-relevance floor; DIAG-H reported no Sharpe; S4's expected ~+0.9 is far above — the floor catches non-survival, not a discovery |
| G-2xcost | >0 AND ≥0.5×(1×) | v2 verbatim | Ratio/zero floor; no realized CS number pre-run |
| G-coststress (CS-A) | net Sharpe AND ann-return both >0 | **zero-floor survival**; 3× long multiplier = microstructure principle | Bar is a zero-floor (weakest non-trivial); no realized CS-A value exists pre-run to fit to; 3× is a-priori "thin half costs ~3× to cross" (see C6 sourcing note) |
| G-maxdd | ≥ −25% | **v2 verbatim** | DIAG-H reported **no maxDD** — cannot have been fitted; = charter "don't draw like an equity bet" |
| G-turnover | ≤ 250×/yr | v2 verbatim | 250× is **3.4× ABOVE** realized 74× — a non-binding ceiling to catch a churn defect, the opposite of a just-below fit |
| G-durable | H1>0 AND H2>0 | charter sign-stability | A **sign** test, not a magnitude near +13.9/+19.5; the engine book could differ from the sleeve, so not pre-guaranteed |
| **G-sample** | span ≥4.0yr AND ≥200 rebals/phase AND **≥12 names/rebal** AND every IS year | Rung-4 sample floor | span ~4.05 post-warmup and ~210 rebals are structural (post-warmup weekly count). **The "≥12 names/rebal" sub-clause sits just under the structurally-determined ~14** (quintile of DIAG-H's 35.5 mean members) → **CONDITION C3** |

Ruling: no HARD threshold is set just below an S4 EDGE number. The single loose anchor is the G-sample "≥12 names/rebal" sub-floor — a **sample-size** floor, not an edge validator, so it manufactures no false-positive edge, but its provenance is realized-value-adjacent and must be re-anchored (C3).

### 2. Crisis throttle (LCDD-z) — PASS on (a) and (b); (c) PASS **conditional on C1+C2**

**(a) Genuinely Layer-2, not a backdoor shared floor — VERIFIED against the record, not the reassurance.** The brief's §2.0 claim that both shared floors are dead is **confirmed exactly** by `CRISIS-FALSIFY-003.md`: Layer-1 GAP-only FAIL→DEAD (entries 25>16, off-episode 4.10%>3% — brief cites "25 … > 16; 4.1% > 3%" ✓); Layer-B DD-from-peak FAIL→DEAD-terminal (CRISIS 12.48%>8%, S+C 27.62%>25% — brief cites "12.5% > 8%; 27.6% > 25%" ✓). CRISIS-FALSIFY-003 §4: "Going into the field: **Layer-2 ONLY** … no shared crisis floor composing under the constructions." So S4 carrying no `s_gap`/`s_dd` and effective scalar = `s_con` is the **AMENDMENT-002 §D min-composition correctly degenerating to `min(s_con)`** — not a resurrected shared floor, not a smuggled one. Fully §C-compliant. (Corollary, noted not faulted: with both shared floors dead there is no crisis-FLAT for S4 — its worst-case de-risk is φ=0.50 gross, never flat. For a **crash-positive** book that earns +54% in crashes, not-flattening is mechanism-appropriate, and the LCDD-z downside-directional read is exactly the down-only design CRISIS-FALSIFY-003 §1 gestures toward. Accepted.)

**(b) Re-pointing leg + flipping tail preserves "not refit" — PASS.** SCUD read the book's exposed SHORT leg's adverse tail (squeeze = P75 upside). S4's exposed leg is the LONG thin cohort; its adverse tail is a dump (P25 downside). Both the leg (the vulnerable/illiquid leg) and the tail-direction (the move that hurts that leg's position) are **mechanically determined by book structure**, not selected by scanning outcomes — the faithful structural mirror. The 8 constants (τ, W, h, q=0.33, m_min, φ, clip) are carried **verbatim** from the sanctioned A3 SCUD spec; because LCDD-z is a **z-score**, the standard-normal quantile anchors (τ_lo≈80th, τ_hi≈95th) transfer distribution-agnostically to the new dispersion series, and the brief pre-registers a **report-don't-tune** rule for a gross coverage mismatch (>40% / mean<0.80). The leg-choice is bundled into the single throttle DOF and carries its own falsifier (§2.2), so it is a pre-registered mechanism hypothesis, not a free fitted DOF. Note q_long=0.33 (a structural third) is a *superset* of the 0.20 quintile long leg — this too is the inherited SCUD convention, not a new choice.

**(c) The crash-positivity "heads-I-win" tension — NOT salvage, PASS *conditional on C1+C2*.** The three dispositions all ship S4, which is the checklist's red flag — but they do **not** all pass: HURTS routes to **MARGINAL** (not-revealable, and names "a different throttle for the tail" as the next target), and the throttle can never manufacture a SUCCESS because §5.1's un-throttled twin independently gates the alpha floors. That is honest pre-registration. **However**, as written the disposition apparatus has two pre-registration defects that would force post-hoc discretion:
- **Overlap (D1):** a THROTTLE-HURTS result whose throttle-off book passes all 13 HARD satisfies BOTH the SUCCESS row ("all 13 HARD on as-shipped = throttle-off") AND the MARGINAL row ("disposition is THROTTLE-HURTS"). Two tiers. → **C1**.
- **Gap (D2):** the HELPS/NEUTRAL/HURTS bins are not exhaustive. With s = Sharpe(throttled)/Sharpe(un-throttled): HELPS needs s≥0.90, NEUTRAL needs s≥0.90, HURTS needs s<0.85 — so **s ∈ [0.85, 0.90) with maxDD not-worse matches no bin** (and a second hole at s>1.10 with Δmaxdd∈[0,2pp)); plus an **overlap** where maxDD worsening <2pp is both NEUTRAL (|Δ|≤2pp) and HURTS (worsens). A disposition landing in the dead zone leaves the top-level map with **no defined "as-shipped" book → no tier at all.** → **C2**.

With C1+C2 applied, HURTS→MARGINAL-only, the bins are MECE, and "throttle-off shipped as a finding" is legitimate (an honest downgrade that flags the next iteration), **not** a heads-I-win construction. Shipping throttle-off at MARGINAL does not breach the §C "every construction ships a throttle" invariant in substance — a throttle *was* pre-registered and falsified; its empirical mis-timing on a crash-positive book is exactly what §C's "falsify your own primitive" is built to surface — **provided** C1 guarantees throttle-off can never masquerade as SUCCESS.

### 3. Ledger integrity — PASS (+1 → 5 is correct; cap-8 honored)

Family-H opened at 4 (S1–S4). EXPLORATION-S4 spends **+1**, the LCDD-z throttle. I scrutinized for smuggled DOF:
- **Engine promotion (return-level residualization → weight-level BTC projection): 0 DOF, accepted.** It is the mandated Stage-1 wiring via the pre-existing sanctioned `apply_beta_neutralization` helper — a single specified path, **no selection from alternatives**. The brief honestly flags (R1, §9.2) that the promotion *does* change realized behavior (which is why G2-CRASH is a genuine unknown, not pre-guaranteed) — that is honesty, not a hidden trial.
- **No-$3M-floor (R2), quintile-equal-weight (R3), funding-per-leg (R4): 0 DOF** — all pin to the DIAG-H *scored object*, not tuned choices; the $3M floor is registered as ledger-neutral CS-L.
- **Cost-stress arms, un-throttled twin, placebo, reversed-direction, leg attribution: 0 DOF (kill-only, ledger-neutral)** — per AMENDMENT-003 §C, correct, and none conditions a design choice. CS-A is HARD-gating but kill-only (no re-tune keys off it); its 3× multiplier is a single a-priori constant, not a scanned parameter (see C6).
- Leg + tail-direction bundled into the one throttle DOF — accepted (one construction, structurally-determined orientation).

Cap-8: opening at 5 leaves headroom for ≤1 Critic-mandated variant; a second throttle spec or signal re-parameterization would be a new trial. Honored.

### 4. Beta-neutrality composition — PASS (ETH-bucket read recommended, C5)

BTC-only minimal-L2 weight projection, with neutrality **measured and HARD-gated**: G1a (β_BTC rolling), G1b (β_ETH rolling), G2-CRASH/G2-MANIA (bucket β_BTC). The **shuffled-signal placebo (§5.2)** is the decisive G3-class defense EXPLORATION-A lacked: same book + same projection + same costs on a cross-sectionally-permuted signal must be (i) beta-neutral (proving neutrality is a projection property, not a signal artifact) AND (ii) zero-edge — over ≥20 pre-registered seeds. Combined with the *separately-measured* crash-bucket β (the placebo alone can't certify crash-specific neutrality — the exact stale-rolling-β mechanism that leaked A's +0.172), the neutrality apparatus is adequate and honest; G2-CRASH is correctly flagged as one of the three real unknowns, not assumed.

Two gaps, neither a charter violation: (i) the placebo null is **one-sided** (fires only on Sharpe>0) — a reliably-negative placebo equally signals a directional plumbing artifact → **C4**; (ii) **ETH is bucketed nowhere** — G2 is BTC-only (charter-consistent), but with a crash-heavy holdout ahead and a BTC-only projection, an ETH crash-beta leak is invisible to the current gates → **C5** (informational report, not a new gate).

### 5. Decision-map completeness — CONDITIONAL (C1 + C2 make it MECE)

Top-level SUCCESS/MARGINAL/FAIL is MECE **except** for the two throttle-disposition defects in §2(c): the SUCCESS↔MARGINAL overlap on THROTTLE-HURTS (D1/C1) and the no-tier gap when the disposition falls in the un-covered [0.85,0.90)× band (D2/C2), which chains up because "as-shipped book" is undefined there. FAIL correctly dominates on any neutrality or control failure. No tier permits post-hoc re-gating once C1+C2 close the overlap and the gap. Fix both and the map is exhaustive and mutually exclusive.

### 6. Contamination / holdout governance — PASS (ensemble-orthogonality flag, C6)

- **Amihud is genuinely-new for the holdout — verified.** PLAN §1.3 family-H row carries two flags (S1 family-A knowledge; S2 DIAG-C sign); S4 is the liquidity sleeve and carries **neither** — consistent with the brief's "cleanest sleeve on provenance." No Amihud/liquidity-provision signal has touched the holdout (IS DIAG-H knowledge is permitted).
- **Regime-composition leak confronted, not hidden:** the crash-heavy/mania-free holdout knowledge + crash-positive book is disclosed head-on with the four §1.3(i)–(iv) defenses (market-only bucketing, pre-committed map, principle-anchored thresholds, edge-not-survival arbiter). Consistent with charter and PLAN §1.3.
- **Token governance stated correctly:** a future S4 reveal spends `MN3-H` and burns family H's *entire* budget (ensemble path + S1/S2/S3 spin-outs die) — matches PLAN §6.1 anti-gaming rule. **This EXPLORATION spends NO token** (`reveal_token=None`, IS-only) — verified against `REVEAL-LEDGER.md` (zero spends). Ensemble-capstone note (S4+G = `MN3-ENSEMBLE`, both tokens atomic) matches PLAN §5.1/§6.3.
- **One forward flag (C6):** Amihud also appears as `amihud30_xz` in family G's 24-feature list (PLAN §3.1). Irrelevant to S4's *IS* validation, but if S4+G are later revealed as an ensemble, the "orthogonal diversification" premise is partially compromised by the shared input — flag now.

---

## CONDITIONS (record as a dated `EXPLORATION-S4-AMENDMENT` before the scored run)

**C1 — MUST (decision-map exclusivity).** Amend the §6 **SUCCESS** row to add: *"AND the §2.2 throttle disposition ∈ {THROTTLE-HELPS, THROTTLE-NEUTRAL} (i.e., NOT THROTTLE-HURTS)."* Rationale: as written, a THROTTLE-HURTS result whose throttle-off book passes all 13 HARD satisfies both SUCCESS and MARGINAL. The brief's own intent (MARGINAL lists HURTS) is that HURTS caps at MARGINAL; SUCCESS must state the exclusion so no result lands in two tiers.

**C2 — MUST (throttle-disposition bins MECE).** Replace the §2.2 HELPS/NEUTRAL/HURTS definitions with a **priority-ordered, exhaustive** partition over (Δmaxdd, s) where s = Sharpe(throttled)/Sharpe(un-throttled), evaluated in this order:
1. **HURTS** if `Δmaxdd < 0` **OR** `s < 0.90` → ship throttle-off, MARGINAL.
2. else **HELPS** if `Δmaxdd ≥ +2pp` AND `s ≥ 0.90` → ship throttled, load-bearing.
3. else **NEUTRAL** (the residual: `Δmaxdd ∈ [0, +2pp)` AND `s ≥ 0.90`) → ship throttled.

This closes the uncovered `s ∈ [0.85, 0.90)` band (a throttle costing >10% carry with no ≥2pp DD gain now correctly routes to HURTS — the honest call for a crash-positive book whose carry the throttle is shaving), closes the `s>1.10 / Δmaxdd∈[0,2pp)` hole (→ NEUTRAL), and removes the small-worsening NEUTRAL/HURTS overlap (any maxDD worsening → HURTS by priority). The HELPS/NEUTRAL boundary is immaterial to the tier (both → SUCCESS), so only the HURTS boundary at s<0.90 is load-bearing; setting it there is gap-free and consistent with the intended 10% carry-tax ceiling.

**C3 — SHOULD (G-sample "≥12 names/rebal" anchor).** Re-anchor the "≥12 names/rebal mean" sub-clause: at the frozen quintile geometry (k=n//5/leg) on DIAG-H's ~35.5 mean membership the realized breadth is ~14, so 12 is a value S4 is pre-guaranteed to clear. Either (a) re-anchor to the structural quintile minimum implied by MIN_MEMBERS=20 → 2·⌊20/5⌋ = **8 names/rebal**, or (b) state the explicit principle fixing 12 (e.g., "the minimum breadth such that no single name exceeds 1/6 of a leg").

**C4 — SHOULD (two-sided placebo null).** Make the §5.2 placebo FALSIFIER two-sided: the placebo passes iff its Sharpe 95% CI includes 0, and FAILS on a Sharpe reliably ≠ 0 in **either** sign. A reliably-negative placebo equally indicates a directional projection/cost plumbing asymmetry; the one-sided test silently passes it. No new compute (the ≥20-shuffle distribution is already produced).

**C5 — RECOMMENDATION (ETH crash-bucket β, informational).** Add a **reported** bucket-conditional β_ETH for CRASH/MANIA (no gate — charter G2 is BTC-only) so an ETH crash-beta leak under the BTC-only projection is measured, not assumed, ahead of a crash-heavy holdout.

**C6 — RECOMMENDATION (ensemble-orthogonality + CS-A sourcing).** (i) Flag in §7 that Amihud is also `amihud30_xz` in family G's feature list; a future S4+G ensemble must measure and disclose S4↔G residual correlation net of the shared Amihud input before claiming a-priori decorrelation. (ii) Cite the CS-A 3× long-leg microstructure basis (trailing spread/depth ratio of thin vs liquid half of the top-40) so it is demonstrably principle-anchored.

---

## Bottom line

The mechanism is IS-validated, the Layer-2-only architecture is correct and independently verified against the terminal floor-death record, the ledger (+1→5) is honest, the token is unspent, and the gate anchoring is — where it could have been gamed — the verbatim charter/v2 value or a zero/sign floor, with the two most-suspect thresholds (Sharpe, maxDD) having no realized DIAG-H value to fit to. **PASS-WITH-CONDITIONS: apply C1 and C2 (MUST) and fold in C3–C4; C5–C6 are recommendations.** With C1+C2 recorded in a dated amendment before the scored run, the "throttle ships regardless" concern resolves into an honest downgrade path, and the pre-registration is airtight. The run may then proceed.

*— Quant Critic, MN3 track, 2026-07-11 (Opus 4.8, Fable-suspended phase). Pre-flight review; read-only; nothing run; holdout sealed; MN3-H unspent.*
