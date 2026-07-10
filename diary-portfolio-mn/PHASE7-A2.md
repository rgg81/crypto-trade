# PHASE7-A2 — QR Formal Verdict on EXPLORATION-A2 (MN track, cross-sectional beta-neutralization)

**Date:** 2026-07-10 · **Role:** Quant Researcher (Phase 7 IS evaluation) · **Track:** baseline-BLIND
MARKET-NEUTRAL (MN). **Contract scored:** `briefs-portfolio-mn/EXPLORATION-A2.md` (frozen 85bbe30f)
+ pre-flight C1–C4. **Inputs:** `EXPLORATION-A2-engineering.md` (QE observed values), `REVIEW-A2.md`
(Critic adversarial review). **Holdout SEALED and unspent; no OOS touched in this document; no
construction change here.**

---

## 1. TIER — plainly: **FAIL**

Frozen §5 decision-map row **"FAIL — other performance HARD"**: a performance HARD gate
(**G-maxdd −25.57% vs the −25% floor**) fails with the edge intact → localize, document, NOT
revealed. **A HARD floor is a HARD floor** (PLAN §5.7); the 0.57pp miss changes nothing about the
tier, and I do not re-weight it against the ten passes.

**This is a clean, information-rich FAIL.** Ten of eleven HARD gates pass — including **G3 on unseen
numbers** (the axis-1 point, adjudicated below), the anti-predecessor gate **G2-CRASH (+0.0088)**,
and durability (funding 6/6 years). The sole breach is a **genuine design boundary**, not a gate
artifact (§3). The scientific yield of the run — that disguised-beta is falsified and the overlay's
dollar-net was an implementation artifact — is recorded in §4 and stands independent of the tier.

### Gate scorecard (verdicts rendered; QE left them blank per scope) — A2-1 PRIMARY

| gate | observed (A2-1) | frozen threshold | verdict |
|---|---|---|---|
| G1a (H) | within 97.0%, max 0.1813 | ≥95% \|β_BTC\|≤0.10 AND max ≤0.20 | **PASS** (within-bound IMPROVED vs Cell-1's 96.0%; max thin: 0.1813 vs 0.20) |
| G1b (H) | within 100.0%, max 0.0957 | ≥95% \|β_ETH\|≤0.15 AND max ≤0.25 | **PASS** (BTC-only projection sufficed — ETH-arm never needed) |
| G2-CRASH (H) | β +0.0088 (n=658) | \|β\| ≤ 0.15 | **PASS (decisive — beta-honest WITHOUT a hedge leg)** |
| G2-MANIA (H) | β −0.0153 (n=999) | \|β\| ≤ 0.15 | **PASS** |
| **G3 (H)** | **rebal-row max 0.0699** (executed targets ≤2.96e-15; all-candle drift 0.2624) | ≤ 0.10 at every rebal | **PASS (Ruling 1 — rebal-row, track-consistent)** |
| G4 (H) | worst-bucket t +0.54 (CRASH) | t > −1.0 | **PASS** (crash t≈0 = neutrality delivered, per §4 relabel) |
| G5 (S) | max bucket share 70.9% (CHOP) | no bucket > 60% | SOFT-FAIL (expected/disclosed) |
| G-sharpe-floor (H) | +1.6784 | ≥ +0.35 | **PASS** |
| G-sharpe-target (S) | +1.6784 | ≥ +0.90 | PASS |
| G-durable (H) | 6/6 yrs > 0 (drip Sharpe informational) | ≥ 5/6 years positive | **PASS (years criterion)** |
| G-2xcost (H) | +1.4619 (0.87×) — GROUND TRUTH | > 0 AND ≥ 0.5×(1×) | **PASS** |
| G-2xcost-target (S) | +1.4619 | ≥ +0.60 | PASS |
| **G-maxdd (H)** | **−25.57%** | ≥ −25% | **FAIL — SOLE HARD BREACH (0.57pp)** |
| G-maxdd-target (S) | −25.57% | ≥ −15% | SOFT-FAIL |
| G-turnover (H) | 54.3× | ≤ 250×/yr | **PASS** |
| G-sample (H) | ≥285 rebals/tranche; 352 names | ≥200 AND ≥40 | **PASS** |
| G-contam (S) | ex-window +2.0652 = 1.23× full | ≥ 0.7× full-IS | PASS |

### G3 measurement ruling (adopted from Critic Ruling 1)
G3 says "|Σw| ≤ 0.10 at **every rebal**" — it scores the **rebal-row**, exactly as Cell-1's 0.2365
and Cell-3's 0.1080 were scored in PHASE7-A (track-consistency). A2-1 rebal-row max = **0.0699**,
PASS. The pass is robust to the stricter inclusive reading (skipped-rebal held-book rows included →
still 0.0699). **Executed rebal targets are dollar-neutral to FP precision (|Σw| ≤ 2.96e-15
everywhere)** — the projection re-solves Σw=0 over valid-price members at each rebal, so the 0.0699
is not a construction residual at all: it is the drifted HELD book measured on 6 in-window
min_members-SKIPPED rebals (feasibility dips 2021-01→02 and 2022-03). The all-candle 0.2624 is
universal intra-hold fixed-share P&L drift, a property of **every** book on this engine, never gated
for any construction. G3 PASSES.

### Both pre-registered contingencies UNTRIGGERED
- **§5.2 axis-2 G3-re-spec CONSIDERATION** — triggered ONLY by "FAIL — G3 at the force-exit floor."
  **G3 PASSED; not triggered.** (And the predicted force-exit floor never materialized — the
  projection eliminated the force-exit mechanism entirely, §5.)
- **§5.3 A2-ETH contingency** — triggered ONLY when G1b/G2-ETH is the sole HARD failure. **G1b 100% /
  G2-ETH within bound; not triggered.**

No contingency fires. Family-A n_eff stays **8** (no inflation).

---

## 2. maxDD is a GENUINE DESIGN BOUNDARY, not a mis-anchored gate (Critic Ruling 2, adopted)

I explicitly reject the tempting reading that G-maxdd is "another EXP-A G3" (a gate colliding with
the construction). It is not:
- The −25% floor is **principle-anchored and GENEROUS** — the charter's MN references run <2–5% DD;
  the floor already grants this book 5×+ that latitude, and it breaches anyway.
- The breach is driven by **real cross-sectional tail risk**: short-meme squeeze dislocations
  (2023-12 −11.23%, 2020-11 −7.94%, 2025-09 −6.38%, 2025-06 −6.14% — Appendix-A). **Beta-
  neutralization structurally does not address this** — it removes MARKET-factor exposure, but a
  short-meme squeeze is an IDIOSYNCRATIC cross-sectional event, orthogonal to β.
- The magnitude is **robust across all three revealed variants**: Cell-1 (hedged) −24.68%, A2
  (β-in-weights) −25.57%, Cell-3 (unhedged) −26.28% — **the funding-carry mechanism, however
  neutralized, draws ~25 ± 1.5%.** The binary pass/fail is fragile to the window choice (Cell-1
  passed by 0.32pp only via the hedge, which PHASE7-A §4.3 already flagged as fragile); the MAGNITUDE
  is the robust, load-bearing finding and it is what matters.

**Consequence:** re-speccing the −25% floor to the observed −25.57% is **REJECTED as post-hoc
re-gating** (an escape hatch; §5.2 was G3-scoped only, never maxDD). This is a design boundary of the
mechanism, to be addressed by a construction with UNSEEN drawdown numbers or accepted as a shelve —
never by moving the gate to the number.

---

## 3. The SURVIVE-≈INTACT §3.1 outcome — the run's scientific result

Independent of the FAIL tier, EXPLORATION-A2 answered the falsifiable-both-ways question PHASE7-A
posed, and the answer is on the record:

- **Net Sharpe +1.6784 ≥ 1.30 AND ratio to Cell-1 = 0.945 → SURVIVE-≈INTACT.** The sharper C4
  comparator (A2 vs the raw unhedged Cell-3) is **0.976**. **Disguised-beta is FALSIFIED at the
  frozen thresholds.** Removing the ~22% directional BTC leg cost only ~2.4–5.5% of Sharpe.
- **The tax lands on the PRICE leg, not the carry.** Funding income +1.59 bps/cd (Cell-1 +1.62) vs
  price +1.66 bps/cd (Cell-1 +1.89) — the projection preserves the funding harvest and gives up
  ~0.23 bps/cd of price mean-reversion P&L. The carry core is intact.
- **The overlay's 0.2365 dollar-net was empirically an IMPLEMENTATION ARTIFACT** (0.2365 → 0.0699 =
  0.30×). Cross-sectional beta-neutralization is the correct MN architecture: it delivers realized-
  beta neutrality in every regime **without a directional hedge leg**, which is precisely the
  anti-predecessor axis this track exists to establish. This is a genuine positive finding.

So: the edge is REAL, DURABLE, and MN-COMPATIBLE — and it FAILS the drawdown floor by 0.57pp on an
intrinsic mechanism boundary. Both facts are true simultaneously and both are recorded.

---

## 4. Mandated relabel + G4/G5 disposition (carried, honest)

- **Regime relabel (PHASE7-A §3, enforced in EXPLORATION-A2 §0.2):** the book is a **CHOP/MANIA
  funding-carry harvester, break-even-neutral in CRASH.** CHOP + MANIA ≈ **96%** of P&L (CHOP 70.9%,
  MANIA 25.0%, CRASH +4.1%). "Pays in all regimes" remains BANNED. Crash-bucket mean +1.13 bps/cd
  full-IS → +0.94 ex-2025-03→12 (n=580) — small and positive, but crash is not where this earns.
- **G4 (PASS, t +0.54 CRASH):** the crash bucket does not significantly lose — neutrality delivered,
  exactly the expected passing outcome under the relabel (a crash t near 0 is neutrality, not a loss).
- **G5 (SOFT-FAIL, CHOP 70.9%):** expected and disclosed — a carry harvester earns most in chop by
  nature. Non-gating. Note the neutralization SHIFTED share toward CHOP (MANIA 28.6%→25.0%) as §0.2
  anticipated, because it shrinks the high-β short-meme mania leg.

---

## 5. Technical-record additions + errata (dated)

### 5.1 §1.6 degenerate-β guard ERRATUM (dated 2026-07-10, ratified — Critic Ruling 5)
My frozen §1.6 degenerate-β guard `det(AAᵀ) < 1e-12 · |M| · Σ(β−β̄)²` is **self-referential**: for
`A = [1; β]`, the Gram determinant identity gives `det(AAᵀ) ≡ |M| · Σ(β−β̄)²` exactly, so the literal
inequality reads `x < 1e-12·x` and can never fire (except FP coin-flips at β≈constant). **ERRATUM:
the intended guard — uniquely pinned by the brief's OWN required unit test (constant β ⇒ fallback
fires, w unchanged) — is `Σ(β−β̄)² ≤ 1e-12 · Σβ²`** (β constant to ~1e-6 relative sd ⇒ the β-row is
rank-deficient). The QE implemented this stable form; RATIFIED as a typo-correction. **All candidate
readings coincide on real data** (a near-constant β cross-section never occurs across 20–40 alts):
observed `n_beta_degenerate_rebal = 0` and `n_projection_collapse_rebal = 0` in all 84 runs (min
pre-rescale gross 0.478 ≫ the 0.10 collapse floor). **Zero effect on any observed number under any
reading.** This erratum is recorded here and does not alter the frozen contract's results.

### 5.2 Warmup / flat-candle correction (Critic Ruling 4 — shared miss, owned)
The brief §7 predicted the programmatic warmup binds at the universe 270-history filter (k≈273). It
does NOT: β_BTC is all-finite at row 135, but the first row with ≥N/2 feasible members is **585
(2020-07-14) → first LIVE rebal k=588**, bound by **panel population + the $3M liquidity floor**, not
the 270-history filter. **I own this miss (shared with the Critic, who endorsed the same premise at
pre-flight).** Consequences, all benign to the verdict:
- The **293 comparability pin HELD** — both A2 and the revealed Cell-1 are scored on the identical
  293 mask, which CONTAINS ~292 flat pre-live candles (both books flat over the same span), so the
  A2-vs-Cell-1 comparison stays candle-for-candle valid.
- **Sharpes carry a ~3% fully-live understatement:** A2 native fully-live window [608, 6574] Sharpe
  = **+1.7307** (n=5967); Cell-1 ≈ **+1.82** inferred. The both-ways ratio is robust (~0.951). The
  headline stays the pinned-mask +1.6784 for comparability; the fully-live +1.7307 is the honest
  point estimate for forward-band anchoring (§6).
- **maxDD is INVARIANT to the flat prefix** (drawdown is measured on the live equity curve), so the
  −25.57% breach and the FAIL tier are entirely unaffected.
- Corrects the EXPLORATION-A engineering wording "all infeasible skips fall before the common metric
  window" → they fall before the book's first LIVE rebal (row 588), which is INSIDE the 293 window.

### 5.3 N20 citation restriction (Critic Ruling 5, adopted)
**A2-N20's G3 (0.1111) and neutrality are a BROKEN-INVARIANT ARTIFACT and MUST NOT be cited** as a
G3/neutrality result without a registered fix: at small member counts the projection unbalances the
long/short legs, and the frozen EXP-A cap then DROPS the residual excess → Σw≠0 at **14 executed
rebals** (max |Σw_target| 0.100), while β-zeroing is erased on **78% of rebals** (cap binds 78.2%;
post-cap target-β residual reaches 0.1467). **A2-N20's Sharpe robustness read (+1.588) stands as
informational only** (it corroborates SURVIVE-INTACT directionally); its G3/neutrality numbers are
excluded from every neutrality claim. The PRIMARY N40 cell is untouched (capDrop=0, cap-bind 1.3%,
residual max 0.0058).

### 5.4 Analytic-2× cross-check (confirms the stateless-only catalog rule)
A2 is STATELESS (no arming) → the analytic twin agrees with ground-truth at 2.91e-4 (N40) / 5.78e-4
(N20), well under 1e-3, ensemble-Sharpe impact 1e-4 — as the new catalog rule predicts for a
stateless construction. Ground truth remains authoritative; the analytic twin validated as a
cross-check. (Contrast EXPLORATION-A's arm-flip drift 2.4e-3 — the rule discriminates correctly.)

---

## 6. Prediction scorecard — my own misses owned

| quantity | my point (band) | observed | assessment |
|---|---|---|---|
| Net Sharpe | +1.45 [+0.9,+1.75] | +1.6784 | band hit; **under-promised edge (honest/conservative direction)** |
| Sharpe ratio A2/Cell-1 | 0.82 [0.51,0.99] | 0.945 | band hit; I predicted a BIGGER tax than materialized — the edge survived more intact than forecast |
| ρ(w_proj,w_raw) | +0.90 [0.75,0.97] | +0.975 | **slightly above band top** — the projection is LESS distorting than I predicted |
| **Realized G3 max** | **+0.10 [0.05,0.15] as a "force-exit floor"** | rebal-row 0.0699 | **band hit but the MECHANISM was WRONG (owned, shared w/ Critic):** I predicted A2 would inherit Cell-3's ~0.108 force-exit floor; the projection re-solves Σw=0 at each rebal over valid-price members, ELIMINATING force-exits entirely (executed targets ≤3e-15). Better than predicted. |
| crash-conditional β | +0.02 [−0.03,+0.08] | +0.0088 | hit |
| full-slice β_BTC | 0.00 [−0.03,+0.03] | −0.0133 | hit |
| **maxDD** | **−20% [−12%,−28%]** | **−25.57%** | **band hit but the POINT was OPTIMISTIC (owned):** I centered at −20%; the mechanism draws ~25%. Under-forecasting the drawdown is the miss that cost the tier. |
| turnover | 60× [45,90] | 54.3× | hit |
| **warmup k / common** | **273/293 (270-history premise)** | **588/293** | **premise MISS (owned, shared w/ Critic):** binding constraint is panel population + $3M floor, not the 270-history filter. Mask pin held; comparability intact. |
| beta-degenerate frac | <1% [0,3] | 0.00% | hit |

Pattern in my misses: I **under-promised the edge** (Sharpe, ratio, distortion all better than
predicted — the conservative direction) but **under-forecast the drawdown** (−20% vs −25.57% — the
direction that cost the tier), and I got the **G3 mechanism wrong** in the optimistic-for-the-book
direction (no force-exit floor). The maxDD point miss is the consequential one; I own it plainly.

---

## 7. Ledger + what does NOT happen

- **Family-A n_eff = 8** (DIAG-A 3 + EXP-A 3 + 1 researcher-DOF + EXP-A2 1; NO contingency inflation —
  neither §5.2 nor §5.3 fired). A drawdown-targeting successor (§7, if the USER authorizes it) would
  be +1 → 9. N20 stays a robustness read (not a selection).
- **Holdout SEALED — the reveal question does not even arise.** No SUCCESS tier → no candidate for
  the family-A holdout-reveal decision. The reveal remains unspent for family A.
- **What explicitly does NOT happen:**
  - **NO maxDD floor re-spec** — REJECTED as post-hoc re-gating (Critic Ruling 2; §5.2 was G3-scoped,
    not maxDD). The −25% floor is not moved to −25.57%.
  - **NO Cell-1 rescue** — Cell-1's G3 is spent (PHASE7-A); A2 is a distinct construction that also
    FAILS, now on maxDD. The 10/11 pass does not buy a partial reveal.
  - **NO automatic A3** — a bounded drawdown-targeting successor is ADMISSIBLE (Critic Ruling 2:
    charter menu-F, +1 n_eff, unseen maxDD numbers, pre-registered target+falsifier, shelve-on-fail)
    but it is a **USER decision**, presented in `FAMILY-A-SYNTHESIS.md`, never automatic.

---

## Bottom line

EXPLORATION-A2 is a **clean FAIL that resolved the family's central scientific question**: cross-
sectional beta-neutralization **solved the G3 problem** (0.2365 → 0.0699, no hedge leg, executed
targets to FP precision), **delivered crash-conditional beta-neutrality** (G2-CRASH +0.0088) — the
anti-predecessor axis, met without a directional leg — and **falsified disguised-beta** (ratio 0.945/
0.976; the carry survives ≈intact, the tax falls on the price leg, funding income preserved). It
fails ONE performance HARD by 0.57pp (maxDD −25.57%), which is a **genuine, robust design boundary**:
the funding-carry mechanism intrinsically draws ~25 ± 1.5% from short-meme squeeze tails that
beta-neutralization structurally cannot address. The family now holds a beta-honest, G3-clean,
survive-intact, durable MN carry book that misses an all-conditions drawdown mandate by a hair. The
decision — shelve, or authorize ONE bounded drawdown-targeting successor — is the USER's, presented
in the family synthesis. Holdout stays SEALED; no work proceeds on family A until the USER chooses.

*— QR, MN track, 2026-07-10. No OOS/holdout touched; no construction changed in this document.*
