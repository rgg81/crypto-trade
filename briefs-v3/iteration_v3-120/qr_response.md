# QR Response — iter-v3/120 — Critic Round-1 PRELIMINARY

**Brief SHA**: `26d99f2`
**Engineering report SHA**: `55f2246`
**Critic PRELIMINARY**: `briefs-v3/iteration_v3-120/review_preliminary.md` (8/8 checks PASS; preliminary direction CONFIRMATION-NO-MERGE per pre-committed F3+F4)
**Two-round protocol**: Round 1 (this response) — NO NEW EVIDENCE. References only committed artifacts in `reports-v3/iteration_v3-{116,119,120}/`, `briefs-v3/iteration_v3-{116,119}/`, and the brief itself.

---

## Position summary

**STAND BY VERDICT** on all five clarifications. Pre-committed binding falsifiers F3 + F4 fire on unambiguous numerical evidence; the Critic's mechanical first-match-wins read is correct on its pre-registered terms. No artifact-grounded basis for reconsideration. The all-time v3 OOS record (+1.6946) is a notable structural finding but does NOT override pre-committed binding falsifiers (the brief itself stated this explicitly in Section 12: "The Critic may override this classification" was an invitation, not a request, and the Critic correctly declined).

The substantive question — whether to authorize a post-/120 /116-only 10-seed methodology iteration (iter-v3/121-METHODOLOGY) before cycle-7 axis selection — resolves to **YES** on artifact-grounded reasoning (see Q1 and Q5 below). This is consistent with the Critic's preliminary one-line recommendation.

---

## Q1 — Attribution gap (central question)

**Pick**: **(b) Authorize a post-/120 /116-only 10-seed methodology iter-v3/121-METHODOLOGY before cycle 7 axis selection.**

**Rationale** (artifact-grounded, no new EDA):

The F3 firing condition mandates "DROP Component B; revert to /116-only for MERGE evaluation" per brief Section 8.4 branch 3/4. Whether or not /116-only-at-10-seed clears /059's BOTH-must-improve gate is the **load-bearing unknown** that determines whether cycle-6 closes with:
- **(i)** CONFIRMATION-NO-MERGE simpliciter (both components evaluated, neither bundles, /059 baseline preserved), OR
- **(ii)** PARTIAL-MERGE on Component A alone (if /116-only-at-10-seed PASSES gates + BOTH-must-improve, Component A merges as a strictly-accretive RULE-layer primitive on /059).

Per brief Section 8.4 branch 3 explicitly: "If /116-only PASSES all gates + BOTH-must-improve → MERGE (Component A only); BASELINE_V3.md updates." This branch is a **pre-committed binding outcome path**, not an aspirational extension. Closing cycle-6 NO-MERGE without running /116-only-at-10-seed would leave a pre-committed branch unevaluated.

Three artifact-grounded reasons to authorize /121-METHODOLOGY:

1. **Component A IS firing in the /120 bundle**: the OOS trade roster (96 trades) contains **8 `no_confirm` exits** vs `take_profit=41`, `stop_loss=41`, `timeout=4`, `end_of_data=2` (per `reports-v3/iteration_v3-120/out_of_sample/trades.csv` exit_reason counts). Single-component /116 at single-seed had 9 no_confirm exits out of 107 trades. The slot-freeing cascade mechanism is mechanically active in the bundle at multi-seed.

2. **The /116-only-at-10-seed cell is the ONLY missing data point** in the cycle-6 multi-seed evaluation grid. We have:
   - /059 (no-A, no-B) at 10-seed: IS +1.0894 / OOS +0.5791 — known.
   - /116 (A-only, no-B) at single-seed (3-seed EXPLORATION): IS +0.6246 / OOS +1.1089 — known.
   - /119 (no-A, B-only) at single-seed (3-seed EXPLORATION): IS +0.8492 / OOS +0.8420 — known.
   - /120 (A+B) at 10-seed CONFIRMATION: IS +0.7293 / OOS +1.6946 — known.
   - **/116-only at 10-seed CONFIRMATION: NOT ON DISK**.

3. **Mode B/C/D in brief Section 7 explicitly pre-registered the /116-only 10-seed re-evaluation**: "If /116-only PASSES BOTH-must-improve → /120 MERGES with Component A only; BASELINE_V3.md updates with RULE-layer single-mechanism baseline. If /116-only also fails → cycle-6 closes NO-MERGE." This branch is binding; the mode tree did not say "do not run it if F3 fires" — it explicitly said run it.

**Why (a) is wrong**: closing cycle-6 NO-MERGE without isolating Component A loses the only piece of information that distinguishes "F3 fired and Component A also fails at 10-seed" from "F3 fired but Component A merges as RULE-layer-only baseline." Those are very different cycle-6 closure characterizations — one yields 0 new baseline ingredients (the all-cycles-6 outcome), the other yields 1 new ingredient (PARTIAL-MERGE on Component A). The next cycle's axis selection depends on which is true.

**The /121-METHODOLOGY spec**: identical /059 baseline runner with the ONE change being `enable_no_confirm_exit=True` (with `trigger_atr=0.50, k_candles=4`); `V3_FEATURE_COLUMNS_TOP_N` reverts to /059's 14-feature set (C6 removed); --n-trials 35, no --exploration, 10-seed unified ensemble; ~3-4h wall-clock per the /059 and /120 baseline. METHODOLOGY classification means it is NOT a new EXPLORATION axis (does not count toward cycle-7's 10/10 cadence), it is a control run to settle a pre-committed component-DROP attribution.

---

## Q2 — F4 knife-edge fail (0.0607)

**F4 is a genuine binding-fail. NOT a knife-edge artifact within compression noise. Pre-commitment is binding contract.**

Three artifact-grounded reasons:

1. **The brief itself selected the tighter +0.79 floor over the looser +0.59 option** with explicit rationale (brief Section 4 F4: "−0.50 would dilute the IS gate to where it tolerates a model that has lost contact with the IS signal entirely; −0.30 retains enough IS discipline to refuse a model where the no_confirm channel has materially broken the IS Sharpe"). The QR pre-committed in writing to the +0.79 floor knowing the +0.59 alternative was available. Renegotiating to +0.59 post-hoc would violate `feedback_no_cheating.md` (parameter renegotiation on OOS-known data).

2. **The IS-leg miss is mechanism-confirmed, not statistical noise**: per engineering report Section 11.3 and per-symbol IS attribution (Section 4 of the engineering report), BCH IS `net_pnl_pct` collapsed from +109.23 to +39.92 (−69.31 pct), with BCH IS trade count actually INCREASING by 6 (+7.2%). The no_confirm channel is cutting BCH trades that would have recovered. This is exactly the regime-cost mechanism F4 was designed to gate on — and it fired as predicted (direction-correct), just severely enough to breach the tighter floor. The miss has a mechanism signature; calling it "compression noise" misattributes a documented IS-cost channel.

3. **`feedback_v3_strict_both_is_oos_baseline.md` is binding contract**: BASELINE_V3.md updates ONLY when both IS and OOS Sharpe improve vs prior baseline (multi-seed mean). F4 is a stricter gate than BOTH-must-improve (+0.79 < +1.0894 baseline IS), so F4 firing AND BOTH-must-improve firing on the IS leg are doubly-binding. Even if F4 had not fired, IS +0.7293 < /059 +1.0894 mandates no baseline update; F4 is the secondary regime-cost-specific gate that confirms the mechanism is the actor, not noise. iter-v3/039 closeout established that OOS-only improvement with IS regression = NO MERGE (memory file: `feedback_v3_strict_both_is_oos_baseline.md`); /120 IS regression −0.3601 vs /059 is materially larger than the F4 miss (−0.0607 vs +0.79), making the BOTH-must-improve verdict robust to any F4-band renegotiation.

**Conclusion**: F4 fires honestly. The brief pre-committed +0.79; observed +0.7293 misses by 0.0607; F4 = FAIL. No post-hoc renegotiation.

---

## Q3 — F3 mechanism scope clarification

**Pick: (a) Component A acts on a C6-reshaped feature landscape (interaction effect — but bundle should STILL be DROPPED per F3 pre-commitment).**

This is artifact-grounded but the verdict does NOT change. Here is why:

**Empirical evidence for interaction (a) over alone (b)**, computed by direct comparison of committed trade rosters in `reports-v3/iteration_v3-120/out_of_sample/trades.csv`, `reports-v3/iteration_v3-116/out_of_sample/trades.csv`, `reports-v3/iteration_v3-119/out_of_sample/trades.csv` (NOT new EDA — set-comparison on existing artifacts):

| Comparison | Shared trades (symbol+open_time) | Trades only in /120 | Trades only in other | Jaccard |
|---|---:|---:|---:|---:|
| /120 (bundle) vs /116 (A-alone, single-seed) | 66 / 96 vs 107 | 30 NEW in bundle | 41 only in /116 | **0.4818** |
| /120 (bundle) vs /119 (B-alone, single-seed) | 71 / 96 vs 103 | 25 NEW in bundle | 32 only in /119 | **0.5547** |
| /116 vs /119 (cross-component overlap) | 67 | — | — | 0.4685 |

The /120 bundle roster is **NOT a near-duplicate of /116-alone** (Jaccard 0.48). If C6 were net-neutral with Component A acting alone (Hypothesis b), we would expect bundle Jaccard with /116 to dominate (≥ 0.75-0.85, with the bundle being essentially /116 plus a small C6-driven perturbation). Instead, the bundle is roughly equidistant from /116-alone and /119-alone, with **30 trades unique to the bundle** that exist in NEITHER component-alone roster. This signature is consistent with hypothesis (a): Component B reshaped the LightGBM loss surface (per /119 diary §5 documented redistribution), which produced a different entry distribution, on which Component A's exit overlay then operated.

**Important caveat**: the comparison is cross-mode (single-seed EXPLORATION /116, /119 vs 10-seed CONFIRMATION /120). Some of the roster divergence is attributable to multi-seed ensemble averaging (different seeds produce different entry distributions; 10-seed averages over a wider set than single-seed). The 30 "NEW" bundle trades may include trades that would have appeared in any of the 10 seeds independently — the multi-seed superset effect. **This is exactly the confound that /116-only-at-10-seed (the /121-METHODOLOGY proposal in Q1) would isolate**: comparing /120 vs /116-only on the SAME 10-seed basis would resolve whether the 30 NEW bundle trades are interaction effect or multi-seed superset effect.

**Why F3 fires regardless of (a) vs (b)**:

F3's mechanism logic is: "C6 cannibalizes regime_momentum_signed_5d allocation WITHOUT contributing direct edge (multi-seed importance share < 5%)." The mechanism statement is **about allocation accounting in the LightGBM split-budget**, not about OOS performance. Both legs of F3 hold cleanly at multi-seed:

- regime_momentum_signed_5d portfolio importance: 171.9 vs anchor 506.67 (−66.1%, threshold < 253.34 ✓)
- C6 portfolio importance share: 2.72% of total 4731.2 (threshold < 5% ✓)

The single-seed pattern at /119 (regime_mom 175.67 ≈ −65.3%; C6 share 2.6%) is **near-identically reproduced** at multi-seed (171.9 ≈ −66.1%; 2.72%). This is the "remarkable numerical stability" the engineering report Section 11.3 noted. F3's conjunctive condition is whether the importance-accounting mechanism is the "cannibal-without-contribution" failure mode — and it is, by the pre-registered numerical thresholds.

That OOS PnL exists doesn't disprove F3's accounting verdict: F3 is a mechanism-attribution gate, not an OOS-performance gate. Per `feedback_v3_promising_feature_mechanical.md`, the FEATURE-MECHANICAL subtype is **non-compoundable-as-signal-source** — it acts as a split-budget redistribution catalyst, not direct edge. F3 was pre-registered precisely to refuse a Component B that achieves the redistribution-catalyst signature without providing direct edge.

**Honest conclusion (engineering report Section 11.3, restated)**: the OOS lift is most parsimoniously attributable to Component A operating on a feature landscape that Component B reshaped. Component B's role is **catalyst, not contributor**. F3 (the pre-committed catalyst-without-contribution gate) fires on this exact mechanism. The bundle WORKS at OOS but C6's mechanism (redistribution catalyst with insufficient direct allocation) does NOT justify its inclusion by the pre-registered falsifier. Component A is the operative mechanism.

This is why /121-METHODOLOGY is the disciplined next step (Q1): it removes C6 and tests whether Component A alone at 10-seed produces the OOS lift, isolating the attribution.

---

## Q4 — BASELINE_V3.md leg

**Confirm: BASELINE_V3.md UNCHANGED at /059. No exception for all-time OOS record.**

Three artifact-grounded reasons (all binding by pre-existing memory rules):

1. **BOTH-must-improve gate is contract** (`feedback_v3_strict_both_is_oos_baseline.md`): IS +0.7293 < /059 IS +1.0894 (Δ −0.3601). Baseline updates require BOTH legs improve; one-leg improvement does not qualify. iter-v3/039 established this rule by NO-MERGE on OOS +1.47 with IS −0.08 vs baseline +0.51/+0.51. /120 is the same shape (large OOS gain, IS regression) — same verdict mandated.

2. **The brief itself pre-registered NO exception** for OOS records (brief Section 8.3): "BASELINE_V3.md updates ONLY if bundle multi-seed IS Sharpe ≥ +1.0894 AND bundle multi-seed OOS Sharpe ≥ +0.5791. If either fails, BASELINE_V3.md DOES NOT update — even if all hard methodology gates and all five falsifiers PASS." Section 8.4 branch 6b explicitly: "If BOTH-must-improve PARTIAL (one leg holds, one misses) → CONFIRMATION-NO-MERGE (partial); BASELINE_V3.md UNCHANGED."

3. **F4 firing independently confirms the IS leg breach**. Even ignoring BOTH-must-improve, F4 (the regime-cost IS floor at +0.79) fires at +0.7293. The IS leg is breached on two independent gates (F4 stricter at +0.79; BOTH-must-improve stricter still at +1.0894). Both gate-trees mandate no baseline update.

**No proposed exception**. The all-time OOS record is a notable structural finding — engineering report Section 3.1 documents +1.6946 vs prior record /059 +0.5791 (Δ +1.12) — and will be recorded in the iter-v3/120 diary as such. But "highest OOS record" is not a pre-registered exception path in BASELINE_V3.md's update tree. Creating an ad-hoc exception now would (a) violate the QR's own pre-commitment in brief Section 8.3, (b) violate `feedback_v3_strict_both_is_oos_baseline.md` directly, and (c) establish a precedent that any future OOS-only-improvement iteration could invoke ("but this is the new record"), eroding the BOTH-must-improve discipline that has been a chronic v3 constraint (brief Section 7 Mode G note: "the BOTH-must-improve gate has been a chronic v3 obstacle — only /028 cleared it").

**Diary handling**: the iter-v3/120 closeout diary will record:
- BASELINE_V3.md UNCHANGED at /059.
- iter-v3/120 OOS Sharpe +1.6946 = all-time v3 record (information-only; does not update baseline).
- F3 fired on sister-redistribution / C6 cannibal-without-contribution.
- F4 fired on IS regime-cost floor (knife-edge by 0.0607).
- Component A re-evaluation deferred to /121-METHODOLOGY (Q1 above).
- Component B (C6) DROPPED per F3 pre-commitment, regardless of /121-METHODOLOGY outcome.

---

## Q5 — Cycle-7 framing

**Pick: (b) Cycle 7 starts with /116-only 10-seed methodology validation (iter-v3/121-METHODOLOGY) to settle the attribution before axis selection.**

Three artifact-grounded reasons:

1. **The /116-only-at-10-seed cell is binding-uncertain** (Q1 above). Until it is evaluated, we cannot characterize cycle-6 outcome:
   - If /116-only-at-10-seed PASSES gates + BOTH-must-improve → cycle-6 delivered 1 PARTIAL-MERGE (Component A as RULE-layer baseline ingredient); cycle-7 axes built on a /116-only baseline.
   - If /116-only-at-10-seed FAILS → cycle-6 closes NO-MERGE simpliciter (0 new ingredients in 10/10 EXPLORATIONs + 1 CONFIRMATION); cycle-7 axes structurally reorient from /059 unchanged.
   Different cycle-6 closure characterizations imply different cycle-7 priorities. Premature axis selection without isolating Component A risks (i) running cycle-7 on a baseline that is wrong by a Component-A-shaped term, or (ii) prematurely declaring cycle-6 a zero-ingredient cycle when 1 ingredient may actually be available.

2. **/121-METHODOLOGY is NOT an axis EXPLORATION** — it is a control run on a pre-committed component-DROP path. Per `feedback_v3_strict_10_to_1_cadence.md`, cycle-7 needs 10 fresh EXPLORATIONs followed by 1 CONFIRMATION. Running a METHODOLOGY iteration first does not consume the cycle-7 EXPLORATION budget; it settles a cycle-6 attribution before cycle-7 begins. (Analogous precedent: iter-v3/018 BOOTSTRAP was a one-time methodology iteration that did not count toward cycle-2's 10/10 EXPLORATION cadence.) Wall-clock estimate ~3-4h per the /059 and /120 baselines, well within the 6h CONFIRMATION cap.

3. **The /119 diary §8.2 cycle-7 candidate axes are NOT yet appropriate**. The /119 diary listed cross-asset/external feeds, longer-cadence labels, NEW model architecture as the cycle-7 candidate menu. These are appropriate cycle-7 axes — but only once cycle-6 closure is fully characterized. Running cycle-7 axis-1 (e.g., cross-asset funding rates) on a /059 baseline that may not be the true cycle-6 baseline (if Component A merges) wastes 35-50 hours of compute on a misaligned anchor. Per `feedback_iteration_quality.md` (QR-bold-changes discipline), cycle-7 axes must be deep-research-grounded structural pivots; they deserve to be tested against the correct baseline.

**Commit to cycle-7 sequence**:
1. iter-v3/121-METHODOLOGY (Component A 10-seed isolation) — settle the attribution. NOT an EXPLORATION axis.
2. iter-v3/122 cycle-7 EXPLORATION axis 1 — selected by cycle-7 QR with full /119 diary §8.2 candidate-axis EDA. Per `feedback_v3_axis_selection_quant_discipline.md`, axis selection requires committed `analysis/iteration_v3-122/*.py` script before brief.
3. cycle-7 follows standard 10/10 + 1 CONFIRMATION cadence per `feedback_v3_strict_10_to_1_cadence.md` and `feedback_v3_cadence_discipline.md`.

**If /121-METHODOLOGY PASSES BOTH-must-improve** → BASELINE_V3.md updates to /121 (RULE-layer single-mechanism baseline, Component A only); cycle-7 EXPLORATIONs anchor against /121 numbers.
**If /121-METHODOLOGY FAILS** → BASELINE_V3.md stays at /059; cycle-7 EXPLORATIONs anchor against /059; cycle-6 characterization is "0 new ingredients in 10/10 EXPLORATIONs + 1 CONFIRMATION + 1 METHODOLOGY"; cycle-7 must structurally reorient (per /119 diary §8.2 candidate axes).

---

## Summary of QR responses

| Q | One-line answer |
|---|---|
| Q1 | (b) Authorize iter-v3/121-METHODOLOGY 10-seed /116-only isolation before cycle-7 axis selection. |
| Q2 | F4 is genuine binding-fail; pre-commitment to +0.79 floor is contract; no renegotiation. |
| Q3 | (a) Interaction effect (bundle Jaccard 0.48 with /116-alone, 30 trades unique to bundle); F3 still fires regardless because the mechanism gate is about allocation accounting, not OOS performance. |
| Q4 | Confirm UNCHANGED at /059. No exception for all-time OOS record; BOTH-must-improve and F4 both mandate no update. |
| Q5 | (b) Cycle-7 starts with /121-METHODOLOGY (Component A 10-seed isolation); fresh /122 EXPLORATION axis selection follows attribution resolution. |

## Position

**STAND BY VERDICT**.
