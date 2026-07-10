# PHASE7-A — QR Formal Verdict on EXPLORATION-A (MN track, funding-carry)

**Date:** 2026-07-10 · **Role:** Quant Researcher (Phase 7 IS evaluation) · **Track:** baseline-BLIND
MARKET-NEUTRAL (MN). **Contract scored:** `briefs-portfolio-mn/EXPLORATION-A.md` + PRE-RUN
AMENDMENT 001 (my frozen brief). **Inputs:** `EXPLORATION-A-engineering.md` (QE observed values),
`REVIEW-A.md` (Critic adversarial review). **Holdout SEALED and unspent throughout; no OOS touched
in this document; no construction change here.**

---

## 1. TIER — plainly: **FAIL**

Frozen §5 decision-map **row 4 — "FAIL — other neutrality HARD"**: a HARD neutrality gate other than
G2-CRASH failed (here **G3**), so the construction does not proceed to the holdout, no automatic A2
fires (A2 was G2-CRASH-scoped and G2-CRASH PASSED), the outcome is localized and documented, and
the sketch is not revealed.

**This is a real FAIL earned by a run, not a declared one.** 10 of 11 HARD gates passed — including
the anti-predecessor gate the whole track exists for (G2-CRASH +0.0103, decisive) — but the gate
map is AND-composed by design: one HARD breach fails the tier regardless of the other ten. I do not
re-weight that. **The G3 gate is now SPENT for Cell 1 on the IS window** — 0.2365 is a known number;
Cell 1 cannot be re-scored on IS.

### Gate scorecard (verdicts rendered; QE left them blank per scope)

| gate | observed (Cell 1) | frozen threshold | verdict |
|---|---|---|---|
| G1a (H) | within 96.0%, max 0.1769 | ≥95% \|β_BTC\|≤0.10 AND max ≤0.20 | **PASS** (thin: +1.0pp; max 0.1769 vs 0.20) |
| G1b (H) | within 100.0%, max 0.1016 | ≥95% \|β_ETH\|≤0.15 AND max ≤0.25 | **PASS** |
| G2-CRASH (H) | β +0.0103 (n=658) | \|β\| ≤ 0.15 | **PASS (decisive — the doctrine axis)** |
| G2-MANIA (H) | β −0.0113 (n=999) | \|β\| ≤ 0.15 | **PASS** |
| **G3 (H)** | **max \|Σw\|/gross 0.2365 (5.9% of rebals breach)** | **≤ 0.10 at every rebal** | **FAIL — SOLE HARD BREACH** |
| G4 (H) | worst-bucket t +0.26 (CRASH) | t > −1.0 | **PASS** |
| G5 (S) | max bucket share 69.6% (CHOP) | no bucket > 60% | SOFT-FAIL (report) |
| G-sharpe-floor (H) | +1.7753 | ≥ +0.35 | **PASS** |
| G-sharpe-target (S) | +1.7753 | ≥ +0.90 | PASS |
| G-durable (H) | 6/6 yrs > 0 (fund Sharpe +16.34 — drip artifact, see §4) | ≥ +0.25 AND ≥5/6 yrs | **PASS on the years criterion** |
| G-2xcost (H) | +1.5616 (0.88×) — GROUND TRUTH | > 0 AND ≥ 0.5×(1×) | **PASS** |
| G-2xcost-target (S) | +1.5616 | ≥ +0.60 | PASS |
| G-maxdd (H) | −24.68% | ≥ −25% | **PASS (thin: 0.32pp)** |
| G-maxdd-target (S) | −24.68% | ≥ −15% | SOFT-FAIL |
| G-turnover (H) | 54.9× | ≤ 250×/yr | **PASS (loose — dead gate)** |
| G-sample (H) | ≥285 rebals/tranche; 352 names | ≥200 AND ≥40 | **PASS** |
| G-contam (S) | ex-window +2.1353 = 1.20× full | ≥ 0.7× full-IS | PASS |

**A2-trigger check (frozen C4 rule):** A2 requires **G2-CRASH FAILS** as condition (i). G2-CRASH
PASSED. Condition (i) is not met ⇒ **no A2.** The C4 rule is respected exactly; there is no
discretion to invoke A2 for a G3 failure.

---

## 2. Central adjudication (Critic's, carried in full) — the breach is BOTH, weighted to mis-spec

The G3 breach is **simultaneously** a gate-vs-doctrine mis-specification (dominant) **and** genuine
residual risk (real, secondary). I adopt the Critic's adjudication verbatim in substance:

**Mechanism (from the QE forensic, §9a).** The alpha book is dollar-neutral EXACTLY — `Σw_alpha ≡
0.0000` at every breach rebal — but it carries structural **negative BTC beta** (long the
structurally-negative-funding majors, short the high-beta memes), reaching **≈ −0.22 in the 2024-25
era**. Cancelling that beta with a spot BTC hedge leg requires a **long BTC notional ≈ +0.22 = the
entire post-hedge dollar-net.** Worst rebals: hedge_btc +0.2155 (2025-04-23), +0.1882 (2024-11-20),
+0.1792 (2024-03-06). A spot-leg beta hedge **mathematically cannot** satisfy |Σw| ≤ 0.10·gross when
|β_alpha| > 0.10 — the two constraints are in direct conflict for this book.

- **(i) Mis-specification vs the charter's OWN doctrine (dominant).** The charter mandates
  **realized-beta neutrality, explicitly NOT dollar-neutrality** (PLAN §1.1: "beta-neutral, not
  merely dollar-neutral"; "'we hedged, therefore we're neutral' is banned" cuts the other way too —
  and so does "dollar-net ≠ risk"). G2-CRASH +0.0103, G2-MANIA −0.0113, G1a 96%/0.1769 all show the
  0.22 dollar-net did **NOT** translate into realized directional risk in any regime. G3 as written
  (a dollar-net bound) indicts the very hedge mechanism the PLAN §4.1 CHOSE, on the axis the charter
  says is not the neutrality axis. This is the /007 G-crash pattern: a gate written from a
  full-sample intuition firing on a regime-tail number that the doctrine gate (G2) already cleared.

- **(ii) But the residual-risk content is genuine (secondary, real).** G1/G2 are **windowed
  averages** — they do not bound the single-candle GAP scenario under beta-estimation error, and a
  standing +0.22 BTC leg carries real **margin, financing, and liquidation footprint** that a
  truly-neutral book would not. The PLAN §4.1 explicitly chose the overlay OVER cross-sectional
  neutralization; this net exposure is that choice's direct, disclosed consequence. G3 is not pure
  noise — it caught something true, even if it caught it on the wrong axis.

**Treatment (mine, following the Critic):** the tier STANDS. The family cannot go to holdout until
the neutrality specification separates **(a) the realized-beta doctrine [passing]** from **(b) a
principle-anchored hedge-notional / margin-footprint bound [the genuine residual]**, OR a
construction meets the frozen G3 outright with unseen numbers.

### 2.1 I own my calibration misses

- **The §1.7 "hedge net small" premise (co-owned with the Critic via the G3 band).** §1.7 asserted
  "hedge legs add net exposure ≈ −book_beta (small)" and PRE-RUN AMENDMENT 001 put the G3-margin
  prediction at 0.05, band [0.02, 0.12]. Both rested on an **unexamined premise**: I extrapolated
  DIAG-A's *full-sample* raw-spread β (−0.055, genuinely small) to the *net exposure* without asking
  what the book beta reaches in a specific era. It reaches −0.22 in 2024-25, and — because G3
  measures |Σw| INCLUDING the hedge leg — the net exposure **IS** that book beta, not a small
  residual of it. This is exactly the /007 rho_bar error class (a regime-tail exposure mis-modeled
  from a full-sample point), and I made it after having cited that very lesson. The Critic co-owns
  the band from pre-flight; the premise was mine.
- **Mechanistic misses (rank-book ≠ decile-probe), honest-direction, non-tier-changing.**
  (a) Turnover 54.9× vs predicted [90×, 200×] — rank weights mutate far less at weekly cadence than
  decile-membership swaps; G-turnover (≤250×) was consequently a **dead gate**, never at risk.
  (b) Cap bind-rate 0.0% at N=40 — the C2 min_members skip-rule excludes precisely the sub-19-member
  region where the cap would bind, so the cap is **structurally inert at N=40** (binds only at N=20,
  22.3%). (c) ETH-arm 2.0% vs [5%, 50%] — the BTC leg alone already neutralizes the residual ETH
  exposure (G1b 100%/0.1016), so the arming rule rarely fires. These do not move the tier, but they
  show I modeled the engine rank-book from the DIAG-A decile probe's mechanics rather than the
  rank-book's own.
- **The CRASH-β prediction was pessimistic (a "good" miss I still own).** I predicted crash β +0.08,
  band straddling 0.15, treating DIAG-A's static-residual +0.172 as predictive. The engine rank book
  measured **+0.0178 UNHEDGED**, +0.0103 hedged — the decile probe and the rank-weighted/capped/
  floored engine book are **different objects**, and I over-weighted the probe number. The doctrine
  axis passed with far more room than I gave it. Lesson for successors: DIAG-A probe geometry does
  not forecast engine-book beta.

---

## 3. Honest attribution — crash-NEUTRAL, not crash-profitable

The mechanism claim in PLAN §2 Sketch A ("who pays us, in ALL regimes … in crash panic the crowded
shorts pay") is now **partially falsified on the earnings axis**, and I correct it here:

- **Crash BETA is clean** (G2-CRASH +0.0103) — the book does not take directional crash risk. Good.
- **Crash PROFIT is a burned-window artifact.** Full-IS CRASH mean +0.54 bps/cd → **−0.01 bps/cd
  ex-2025-03→2025-12** (n=580). The crash bucket earns **nothing** outside the revealed window; it is
  exactly break-even-neutral. The G4 pass (t +0.26) is likewise ex-window ≈ 0.
- **98% of P&L is CHOP + MANIA** (CHOP 69.6%, MANIA 28.6%, CRASH +1.8%). This is a **CHOP/MANIA
  carry harvester**, not an all-conditions earner. The correct mechanism statement, which every
  successor brief MUST carry, is: **"pays in CHOP and MANIA; break-even-NEUTRAL in CRASH"** — the
  funding-collects-in-crash leg is offset by the price giveback there (DIAG-A already showed CRASH
  price −22.7 bps vs funding +13.3 bps at the decile level; the engine book nets it to flat).
- **Directly adverse forward note.** The sealed holdout (2026+) is **crash-heavy** (2025-11→2026-07
  was a crash-dominated regime). A CHOP/MANIA earner's best buckets are exactly what a crash-heavy
  holdout starves. This is a material, disclosed forward risk that discounts any future reveal of
  this earner — the adverse regime for this book is precisely the out-of-sample regime.

---

## 4. Technical-record additions (catalog-worthy)

1. **Analytic cost twins are valid ONLY for STATELESS constructions.** EXPLORATION-A exposed a
   **second** invalidation channel beyond /007's equity-renormalization drift: the ETH arming rule
   reads the book's OWN past cost-bearing net returns, so under a cost change (2×) a few arming
   DECISIONS flip and weights genuinely differ (drift 2.4e-3 on the two arm-flip cells vs 2.6e-4 on
   pure-fixed-share cells). **New rule: any stateful control that reads realized cost-bearing returns
   (hedge arming, dd-brake, vol-target) mandates GROUND-TRUTH cost re-runs; analytic twins are
   stateless-only.** Pre-flight C1 (ground-truth re-runs) saved this run — the ensemble-Sharpe impact
   was negligible (+1.5619 analytic vs +1.5616 truth), but the principle is now load-bearing.
2. **G-durable's +16.34 "Sharpe" is an income-drip artifact — a consistency check, NEVER a
   forecast.** The uncosted funding income of a ~dollar-neutral book is a near-deterministic drip
   (mean +1.62 bps/cd, tiny σ), so its Sharpe is meaningless as a magnitude. **What G-durable
   validly certifies is the 6/6-years-positive count** — the carry is present and positive every IS
   year (incl. 2022, when TOTAL Sharpe was −0.165). I set the G-durable Sharpe threshold (+0.25)
   without recognizing it would be cleared by a drip regardless; the years-count is the real gate and
   it passed on its merits. Successors should gate G-durable on the years-positive count only.
3. **Thin PASS margins flagged (fragile, do not expect OOS-stable).** G1a within-bound 96.0% vs the
   95% floor (+1.0pp) and max|β| 0.1769 vs 0.20; maxDD −24.68% vs −25% (0.32pp — and the unhedged
   Cell 3 ensemble was already −26.28%, so the hedge pulled Cell 1 inside the floor by a hair). Both
   PASS, neither is tier-changing, but both are **fragile PASSes** that would inform (and discount)
   any future reveal — they are not evidence of robust margin.

---

## 5. PATH — recommendation (labeled), and what does NOT happen

**RECOMMENDATION (QR, Phase 7): adopt Critic AXIS 1 — a NEW construction with cross-sectional
beta-neutralization of the alt weights** (the PLAN §4.1-REJECTED alternative), as the next MN
EXPLORATION. This is a recommendation, not an action; it is registered as the next brief before any
run.

**Reasoning:**
- **It generates UNSEEN G3 numbers on a genuinely different construction, leaving the frozen G3 gate
  untouched.** Cross-sectional neutralization folds the BTC-beta cancellation INTO the alpha weights
  (adjust each name's weight so Σ w_i·β_i ≈ 0 subject to Σ w_i = 0), so there is **no separate hedge
  leg carrying the dollar-net** — G3's |Σw| is structurally near-zero by construction rather than by
  a spot leg fighting the constraint. This is the methodologically cleanest response: no re-gate, no
  fit-to-0.2365, a real experiment on a new object.
- **It tests the sharper question the breach exposed:** can this carry edge be neutralized WITHOUT a
  ~22% directional BTC leg? If cross-sectional neutralization holds the realized-beta neutrality that
  the overlay already achieved (G2-CRASH passed decisively) AND clears G3 with unseen numbers AND
  retains the carry Sharpe, we learn the overlay's dollar-net was an implementation artifact, not an
  inherent property of the edge. If the carry COLLAPSES without the directional leg, we learn the
  edge was partly a disguised beta bet — a genuine, valuable NEGATIVE finding either way. Falsifiable
  in both directions.
- **Axis 3's honest relabeling is folded in, not chosen standalone.** The successor brief MUST
  correct the regime claim to **"CHOP/MANIA carry harvester, crash-break-even-neutral"** (§3) — this
  is mandatory in ANY successor regardless of which axis is registered, because "pays in all regimes"
  is now falsified for CRASH. Axis 3's optional dispersion-conditional crash de-risk is carried as a
  candidate risk-primitive INSIDE the axis-1 successor, not as a separate track.
- **Axis 2 (doctrine-motivated G3 re-specification) is SECONDARY, not chosen now.** It is admissible
  ONLY as a dated PLAN-AMENDMENT (+1 n_eff, number NOT fitted to 0.2365, denominator pinned, scored
  only on unseen data, contamination disclosed). It is deferred because it spends a DOF and carries
  re-gating optics even when disciplined; the correct first move is the construction that leaves the
  gate untouched. If axis 1 also breaches a *correctly specified* net/margin bound, axis 2 becomes
  the live fallback with the discipline above.

**What explicitly does NOT happen:**
- **NO holdout spend.** The family-A reveal stays sealed; a correctly-specified neutrality PASS on
  UNSEEN construction numbers is a precondition, and none exists yet.
- **NO Cell-1 rescue.** The G3 gate is spent for Cell 1 on IS; 0.2365 is known and cannot be
  re-scored, re-weighted, or argued past. The 10/11 pass does not buy a partial reveal.
- **NO gate re-fit to 0.2365.** No G3 threshold is moved to accommodate the observed breach (that is
  the forbidden IS re-gate). Any future G3 re-spec (axis 2 only) is principle-anchored and
  unseen-data-scored.
- **NO A2.** A2 was G2-CRASH-scoped (frozen C4); G2-CRASH passed, so A2 is not on the table.

---

## 6. Ledger + honest forward band (information only)

- **Family-A n_eff ≈ 7 DOF** — DIAG-A 3 cadence cells + EXPLORATION-A 3 construction cells + 1
  researcher-DOF. **+1 if the axis-2 G3 re-spec path is ever taken.** (On the record, Critic check 9:
  promoting the N=20 robustness column to PRIMARY would be a selection event requiring re-ledgering
  — N=20 stays a robustness read.)
- **Honest forward band (Critic's, carried as INFORMATION for a FUTURE reveal decision only — NOT a
  forecast, NOT a reveal authorization):** IF a frozen-gate-passing (correctly-specified-neutrality)
  version ever reaches the holdout, expect **~+0.5 to +1.1 Sharpe, central ~+0.75–0.80.** Basis: the
  funding leg is a durable core (positive 6/6 IS years); the price-mean-reversion leg is fragile
  (2022 TOTAL Sharpe −0.165); phase-luck is already removed by the 21-tranche construction; and the
  crash-heavy holdout is the adverse regime for a CHOP/MANIA earner (§3). The full-IS Cell-1 +1.7753
  is NOT the forward expectation — it is a phase-honest but regime-favorable IS number on a
  construction that failed neutrality specification.

---

## Bottom line

EXPLORATION-A is a **clean, informative FAIL**: the funding-carry edge is real, cost-robust, and —
on the axis this track exists to defend — **genuinely beta-neutral including in crashes** (G2-CRASH
+0.0103, the decisive win). It failed the ONE gate that measures dollar-net rather than realized
beta, because the spot-BTC-hedge overlay must run a ~22% directional leg to cancel the book's
structural negative beta. That is a specification tension between the frozen G3 gate and the PLAN's
chosen hedge mechanism, plus a real (secondary) margin-footprint risk. The family is **alive**; the
next step is a cross-sectional-neutralization construction that removes the directional leg by
design and re-measures G3 on unseen numbers, carrying forward the corrected "CHOP/MANIA harvester,
crash-break-even-neutral" claim. Holdout stays sealed.

*— QR, MN track, 2026-07-10. No OOS/holdout touched; no construction changed in this document.*
