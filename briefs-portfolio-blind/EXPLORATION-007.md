# EXPLORATION-007 — All-21-Phase Equal-Weight ENSEMBLE of the Frozen L1 (staggered rebalancing; IS-only, pre-registered)

## Section 0 — Provenance & scope (pre-registration)

- **Frozen:** 2026-07-10, BEFORE any ensemble backtest runs. This brief is the frozen contract; the
  engineer runs the matrix ONCE and the results are scored against the gates below. **No post-hoc
  tuning is permitted** — any change to construction, controls, gates, month lists, the decision map,
  or the forward-recommendation logic after the run invalidates the pre-registration and must be
  recorded as a new EXPLORATION.
- **Track:** baseline-BLIND top-20 L/S portfolio (worktree `quant-portfolio-blind`).
- **BASELINE-BLINDING intact.** Designed against `blind_*` modules + the blind diaries
  (DIAGNOSTIC-003, PHASE7-006 incl. both addenda, REVIEW-006 incl. ADDENDUM 2) and the committed
  `paper-l1/phase_sweep_is.csv` only. **No baseline artifact read** (`BASELINE_PORTFOLIO.md`,
  `analysis/portfolio/iter_*.py`, `diary-portfolio-top20/`, sibling `quant-portfolio*` worktrees —
  none touched).
- **OOS QUARANTINE — this is an IS-ONLY phase end to end. There is NO OOS reveal in EXPLORATION-007**
  (same posture as /006). `OOS_CUTOFF = 2025-03-24` is sealed; `CONFIRMATION-005.md` (burned OOS
  numbers) was NOT read. Every number produced by the matrix is computed on candles
  `open_time < 2025-03-24`. The verdict semantics below are **IS design-validation only**, explicitly
  NOT a deployability claim.
- **Backtests run by this QR: ZERO.** The per-phase IS ingredients already exist in
  `paper-l1/phase_sweep_is.csv` (the committed 21-phase sweep, REVIEW-006 ADDENDUM 2). The engineer
  runs the single frozen ensemble pass against this brief. No side-probes.
- **L1 ingredients FROZEN.** This exploration changes ONLY the phase-aggregation structure. No C1/C2
  parameter, no signal/universe/cost/gross/fraction/funding change. The tranche is the byte-frozen L1.
- **Do NOT touch the running forward-validation.** `PROTOCOL-L1-FORWARD` (T0 = 2026-07-15, single
  Wed@00h book) is a SEPARATE artifact. Its relationship to this design iteration is discussed in §5 as
  a *recommendation-logic* item to be decided by the USER after this verdict — never an automatic
  action of this brief. `PROTOCOL-L1-FORWARD.md` was deliberately NOT read/edited.

### 0.1 The design thesis (one paragraph)

REVIEW-006 ADDENDUM 2 split the /006 verdict cleanly. On the **DESIGN/MECHANISM** axis the C1+C2
overlay is phase-robust — L1−V0 is positive at **21/21** rebal phases (mean +0.614), turning a
phase-fragile base (V0 negative at 4/21) into a **21/21-positive-Sharpe** book (F10). On the **LEVEL**
axis the frozen headline is a favorable, never-chosen phase draw: the Wed@00h +1.164 Sharpe /
−28.58% maxDD ranks 8/21 in Sharpe, and L1 maxDD **breaches −35% at 7/21 phases (to −70.4%; phase
mean −37.3%)** — F7, the phase-fragility of the tail. ADDENDUM 2 Q3(iv) named the **all-21
equal-weight ensemble** "a genuinely more robust NEW construction requiring full re-validation." This
phase builds and IS-validates exactly that construction. The mechanism is textbook **staggered
rebalancing / overlapping portfolios** (the same variance-reduction device as Jegadeesh-Titman
overlapping momentum portfolios and the standard practitioner "tranche the rebalance across the cycle"
fix): hold 1/21 of gross in each of the 21 weekly phases, so the book rebalances 1/21 of itself every
8h candle. By construction this **removes phase luck** — the ensemble level BECOMES the phase-agnostic
average — and the open question is whether **time-diversification of entry points also clips the maxDD
tail**, or whether the 7/21 deep-DD phases drag the ensemble through the floor because the drawdowns
are synchronized regime losses that averaging cannot diversify.

---

## Section 1 — Hypothesis + crypto-native mechanism

**H1 (LEVEL — nearly-determined, NOT the discovery).** The ensemble Sharpe is set, up to a small
diversification adjustment, by the already-observed phase mean **+0.947** (F-sweep). Averaging 21
imperfectly-correlated tranche return streams reduces the ensemble vol by the diversification factor
`sqrt((1 + 20·rho_bar)/21)` relative to a single tranche, lifting the Sharpe modestly above the phase
mean. Because the tranches hold **nearly-identical portfolios shifted by ≤ 6.7 days** (max phase
offset 20 candles), `rho_bar` is high and the lift is small. This is an **arithmetic consequence of
the sweep, not a finding** (see §2).

**H2 (maxDD TAIL — the genuine experiment).** *Mechanism, crypto-native:* the /005 book's drawdowns
are driven by **alt-mania short-squeeze months** (2024-11, 2021-03, 2020-11, 2024-05, 2023-12 —
DIAGNOSTIC-003 §3), month-scale regimes in which every phase is short-exposed. The rebal PHASE only
decides the intra-squeeze *timing* — whether a given tranche's short is entered/exited before or
through the blow-off. ADDENDUM 2's dispersion evidence (**2024-11 swings 35.3pp across phases**) shows
that timing dispersion is large and concentrated in exactly these squeeze months. **If** that
dispersion is idiosyncratic across phases, the ensemble averages it out and the maxDD tightens toward
the good-phase / better-than-median region (time-diversification clips the tail). **If** the
squeeze losses are synchronized (all 21 phases bleed in the same calendar window, differing only in
depth), averaging buys only the ~6% vol reduction and the ensemble maxDD lands near the phase mean
**−37.3%**, breaching the floor. **This is F7's open question, and it is what the gates bind on.**

**H3 (robustness — strengthened design axis).** The ensemble should inherit F10's phase-robust
overlay: all IS years positive, crash-month strength preserved (the short leg is the crash friend at
every phase — DIAGNOSTIC-003 §2), mania squeeze mitigated. These are directional predictions the
matrix scores, not the crux.

Cites: ADDENDUM 2 (Q3(iv) ensemble ruling; F7 maxDD phase-fragility; F10 overlay robustness);
DIAGNOSTIC-003 §2/§3; `paper-l1/phase_sweep_is.csv`.

---

## Section 2 — HONESTY SECTION (load-bearing — the Critic will attack here)

**The 21 ingredients' IS Sharpe and maxDD are ALREADY OBSERVED.** The committed sweep
(`phase_sweep_is.csv`, REVIEW-006 ADDENDUM 2) reports every tranche's warmup=63 Sharpe and maxDD. The
ensemble is a **deterministic function** of those 21 already-seen streams. Therefore:

**(a) The ensemble's Sharpe LEVEL is known ex-ante and is NOT a discovery.** The ensemble mean return
equals the arithmetic mean of the 21 tranche mean returns; its Sharpe equals the phase-mean Sharpe
`sqrt(21/(1 + 20·rho_bar))`-scaled by the modest diversification-of-vol factor. With `rho_bar` high
(nearly-identical holdings shifted ≤ 6.7 days), that factor is ~1.03–1.06. **Pre-stated expected
range: ensemble Sharpe +0.90 … +1.08, point +0.98** — anchored at the observed phase mean **+0.947**
plus a small, bounded lift. A headline anywhere in that band **confirms arithmetic, not edge**. A
Sharpe near the predicted level therefore **passes NO gate by itself**: G-sharpe-floor (§4) is set
where it can only catch an *implementation catastrophe* (an averaging/sign bug, cost charged 21×, a
misaligned grid), never certify a new finding. **Do not read a passing headline as an EXPLORATION-007
result.** (The genuine deflation vector — phase luck — was already booked against the *single-phase*
+1.164 in ADDENDUM 2; the ensemble does not re-earn it, it *pays it down* by construction.)

**(b) What IS unknown and is being tested (the gates bind here):**
1. **Ensemble maxDD — THE unknown.** No prior artifact ever computed it. Single-phase maxDD ranges
   −21.3% (best) → −70.4% (worst), phase mean −37.3%, median −32.2%, **7/21 breach −35%**. Does the
   ensemble land in the diversifiable region (≤ −30%, time-diversification clips the tail) or near the
   synchronized-regime phase mean (breaching −35%)? This is F7 resolved.
2. **Worst single month.** Does averaging the 35.3pp-of-phase-dispersion squeeze months (e.g. 2024-11)
   shrink the worst month below the single-phase figures?
3. **Bucket behavior on the FROZEN month lists.** Crash-bucket (20mo) and mania-bucket (13mo)
   ensemble means + leg attribution — never computed for any ensemble.
4. **Aggregate turnover** of the staggered book (COST-CONSERVATIVE no-netting, partially offset by the
   costless-1/21-maintenance idealization — see §4 G-turnover).
5. **2×-cost survival** of the ensemble.
6. **Per-year profile** of the ensemble (all IS years ≥ 0?).

**The gates in §4 bind on 1–6, NOT on the Sharpe level.** The FALSIFIER (§4/§5) is explicit: if
ensemble maxDD still breaches −35%, the phase-tail is NOT time-diversifiable — a genuine negative
finding, documented, no tuning.

**(c) Selection honesty.** The ensemble is **selection-free**: equal-weight over ALL 21 phases is the
one aggregation that chooses nothing. We are NOT adopting Wed@08h (the sweep max) or any best-of-k
phase — that would convert the admissible sweep into a best-of-21 search and void ADDENDUM 2 ruling 1.
The only researcher DOF this phase introduces is the decision to build the ensemble at all + the
equal-weight rule (counted in §6). No parameter is tuned.

---

## Section 3 — Pre-registered predictions (scored after the run)

Point estimates + bands, frozen pre-run, derived from `phase_sweep_is.csv` + correlation reasoning, so
prediction hits/misses are scorable. `rho_bar` = mean pairwise Pearson correlation of the 21 tranche
return streams on the common slice (the engineer computes it — §7 — feeding the scoring of this table).

| Quantity | Point | Band | Reasoning |
|---|---:|---|---|
| **rho_bar** (mean pairwise tranche corr) | **+0.88** | [+0.80, +0.94] | near-identical holdings shifted ≤ 6.7d; divergence concentrated in squeeze months (2024-11 35.3pp) → high but well below 1 |
| **Ensemble Sharpe** (headline) | **+0.98** | [+0.90, +1.08] | phase mean +0.947 × diversification factor `sqrt(21/(1+20·rho_bar))` ≈ 1.03–1.06 |
| **Ensemble vol** (÷ single-phase typical) | **0.94×** | [0.88×, 0.98×] | `sqrt((1+20·rho_bar)/21)`; modest because rho_bar high |
| **Ensemble maxDD** ← the crux | **−28%** | **[−22%, −36%]** | smoother averaged path + squeeze-month timing averaged out, bounded below by synchronized regime loss; band deliberately straddles the −35% HARD floor AND the −30% SOFT floor |
| **Ensemble 2×-cost Sharpe** | **+0.86** | [+0.76, +0.96] | headline − same per-doubling cost drag as single-phase Wed@00h (+1.164 → +1.028, drag ≈ 0.14); turnover ≈ single-phase |
| **Ensemble turnover** (ann one-way) | **+50x** | [+48x, +55x] | staggered book: 21 tranches × (1/21 gross) × ~50x each = ~50x aggregate (§4 verification); no-netting → this is the conservative UPPER bound |
| **Ensemble crash-bucket mean** (20mo) | **+1.7%/mo** | [+1.3%, +2.1%] | phase-ensemble of single-phase crash P&L; short leg is crash friend at every phase |
| **Ensemble mania-bucket mean** (13mo) | **+4.8%/mo** | [+3.8%, +5.8%] | phase-ensemble of C1+C2 mania footprint (Wed@00h L1 mania +5.83%; other phases lower) |
| **Ensemble worst single month** | **−11%** | [−8%, −14%] | averages the 35pp squeeze-month phase dispersion → below single-phase L1 −12.72% likely |
| **Min per-year Sharpe** | **+0.2** | all years ≥ 0 | 21/21-positive overlay + averaged base → all years positive; 2023 is the thin one |

**Modal outcome I expect:** PASS all 8 HARD gates; G-dd-floor (−35%) PASS with margin; G-dd-target
(−30%) a coin-flip; Sharpe lands at ~phase-mean (confirming arithmetic, per §2a). The information is in
whether maxDD clears −30% (clips the tail → strong preferred design) or sits in (−35%, −30%) (matches
phase-mean → preferred on phase-luck-removal only) or breaches −35% (FALSIFIER).

---

## Section 4 — Pre-registered GATES (frozen thresholds, IS-only, common warmup=63 slice)

Evaluated on **ENSEMBLE-L1** (the equal-weight 21-phase book). References that require a baseline use
**V0-ENSEMBLE** — the equal-weight 21-phase ensemble of the /005 base (no C1/C2) — NOT single-phase
V0, so candidate and reference are apples-to-apples (both are 21-phase ensembles). **HARD = fail kills
the candidate (FAIL). SOFT = report + set the SUCCESS/PARTIAL tier.**

| # | Gate | Metric | Threshold | H/S | Rationale |
|---|---|---|---|---|---|
| **G-years** | per-year ensemble Sharpe | every IS year {2020,2021,2022,2023,2024,2025Q1} **≥ 0** | **HARD** | user mandate #1: all years positive incl. worst regimes |
| **G-crash** | ensemble crash-bucket (20mo) mean monthly ret | **≥ +1.55%/mo AND > 0** | **HARD** | preserve crash alpha; same absolute floor as /006 (60% of single-phase V0 +2.59%). Also REPORT vs V0-ENSEMBLE crash for context |
| G-crash-win | ensemble crash-bucket monthly win rate | ≥ 55% | SOFT | crash texture |
| G-crash-leg | ensemble crash-bucket aggregate short_px | > 0 | SOFT | short leg still the crash friend |
| **G-mania** | ensemble mania-bucket (13mo `MANIA_MONTHS_FROZEN`) mean monthly ret | **≥ V0-ENSEMBLE mania mean + 2.0 pp** (predicted V0-ENS ≈ +2.5%/mo ⇒ threshold ≈ **+4.5%/mo**) | **HARD** | mechanism-efficacy, ENSEMBLE-vs-ENSEMBLE reference (see note ‡) |
| G-mania-worst | ensemble mania-bucket worst single month | strictly better than V0-ENSEMBLE mania worst month | SOFT | operationalizes "fix the squeeze" |
| **G-sharpe-floor** | ensemble headline Sharpe | **≥ +0.60** | **HARD** | catches implementation catastrophe ONLY; nearly-guaranteed given ex-ante ~+0.95 (§2a) — passes NO discovery |
| G-sharpe-target | ensemble headline Sharpe | ≥ +0.90 | SOFT | level came in at the predicted phase-mean → SUCCESS tier |
| **G-2xcost** | ensemble 2×-cost Sharpe | **≥ +0.45** | **HARD** | cost-fragility floor; nearly-guaranteed (turnover ≈ single-phase) |
| G-2xcost-target | ensemble 2×-cost Sharpe | ≥ +0.75 | SOFT | comfortable cost survival → SUCCESS tier |
| **G-dd-floor** | ensemble maxDD | **≥ −35%** | **HARD** | THE load-bearing gate — the whole point is beating the single-phase tail (phase mean −37.3%, 7/21 breach). Breach ⇒ FALSIFIER (§5) |
| G-dd-target | ensemble maxDD | ≥ −30% | SOFT | time-diversification CLIPPED the tail (beat median single phase) → ENSEMBLE-L1 strongly preferred |
| **G-turnover** | ensemble turnover ann one-way | **≤ 100x/yr** | **HARD** | cost-fragility guard; predicted ~50x (verification ‖) |
| **G-worst-month** | ensemble worst single IS calendar month | **≥ −15.0%** | **HARD** | no new tail via averaging artifact; improve on single-phase V0 −16.35% |

**8 HARD** (G-years, G-crash, G-mania, G-sharpe-floor, G-2xcost, G-dd-floor, G-turnover,
G-worst-month) + **6 SOFT**.

**‡ G-mania reference (define precisely).** The 13-month `MANIA_MONTHS_FROZEN` bucket is **inherited
verbatim** (market-only C1-coverage≥0.40 rule, `blind_mania_rule.py`) — NOT redefined for the
ensemble. Only the *baseline within that bucket* changes: for the ENSEMBLE the reference V0 is the
**V0-ENSEMBLE** mania mean (the equal-weight 21-phase ensemble of the V0 base, bucketed on the same 13
months, common slice), not single-phase Wed@00h V0's +2.524%. Gate = `mania(ENSEMBLE-L1) ≥
mania(V0-ENSEMBLE) + 2.0 pp`. The +2.0pp margin is inherited unchanged from /006's frozen
pre-registration. **This remains a MECHANISM-EFFICACY test, not independent regime alpha** (12 of 13
mania months are short-loser months where C1 helps by construction; only 2020-12, short_px +0.143, is
a clip-hurts winner) — a G-mania pass is NOT evidence of alpha on an independently-defined regime.

**‖ G-turnover verification (reasoning REQUIRED in the report).** Naive intuition "21 tranches × 50x
÷ 21" is right but must be shown: turnover is scale-free (traded notional ÷ gross). Ensemble one-way
turnover = Σ_p [(1/21)·gross · T_p^ann] / gross = (1/21)·Σ_p T_p^ann ≈ (1/21)·21·50 = **50x**. The
"÷21 then ×21" cancels — the staggered book trades the SAME ~50x/yr as a single phase, just spread one
tranche per candle. **COST-CONSERVATIVE (no-netting): a real implementation nets internal crossings
between tranches** (when tranche p buys name X while tranche q sells name X, the exchanged notional is
smaller) → real turnover ≤ 50x. We do NOT model netting; the reported ~50x and all cost-bearing
metrics (headline Sharpe, 2×-cost Sharpe) are a **disclosed conservative (pessimistic) bias**. Passing
gates under no-netting is a lower bound on the real book. **Offsetting idealization (Critic Condition
C):** the mean-of-returns ensemble holds constant equal 1/21 cross-tranche weights, implicitly assuming
**costless maintenance** of those weights (no rebalancing charge to keep each tranche at exactly 1/21
as their equities drift apart) — a small OPTIMISTIC idealization that partially offsets the no-netting
CONSERVATIVE bias. With tranches ~88–94% correlated both effects are tiny; the net is likely still
conservative.

**FALSIFIER (frozen, explicit).** If **ensemble maxDD < −35%** (G-dd-floor breach), the conclusion is
that **the phase-tail is NOT time-diversifiable** — the squeeze-month drawdowns are synchronized
regime losses that staggered rebalancing only vol-smooths (~6%), not tail-diversifies. This is a
genuine, publishable **NEGATIVE finding** about the construction's irreducible tail. **Document it; do
NOT tune** (no phase subset, no weight scheme, no floor widening). It does not become a new
EXPLORATION's excuse to search for a "better ensemble."

---

## Section 5 — Frozen decision map + FORWARD-RELATIONSHIP (decided NOW)

### 5.1 IS interpretation tiers (design-validation only; NO OOS)

**The discriminating axis is maxDD** — the one genuinely-unknown observable (§2). The Sharpe/2×-cost
SOFT targets (G-sharpe-target ≥ +0.90, G-2xcost-target ≥ +0.75) are **near-known ex-ante to pass**, so
they do **NOT** gate the tier — they are demoted to **prediction-scoring lines** (§3), reported but
not tier-determining. Letting an already-observed quantity co-determine SUCCESS would contradict §2
("Sharpe passes no gate").

| Outcome | Condition (maxDD-discriminated) | Interpretation |
|---|---|---|
| **SUCCESS** | ALL 8 HARD pass **AND** G-dd-target (maxDD ≥ −30%) | Time-diversification clipped the tail: the ensemble beats the median single-phase maxDD. **ENSEMBLE-L1 becomes the track's preferred design on the maxDD/robustness axis.** Trigger the §5.3 forward-switch recommendation (strong). |
| **PARTIAL** | ALL 8 HARD pass **BUT** maxDD in (−35%, −30%] | Phase luck removed and tail honest, but maxDD only matched the phase mean (didn't beat the best phase). ENSEMBLE-L1 is still **preferred on phase-luck-removal grounds** (it eliminates the single largest deflation vector ADDENDUM 2 identified). Present both books to the user (§5.3). |
| **FAIL** | ANY HARD fails | Localize: **G-dd-floor breach → FALSIFIER** (phase-tail not time-diversifiable; §4); G-years → a regime broke; G-crash → crash alpha lost in aggregation; G-mania → squeeze not fixed in aggregate; G-worst-month → averaging artifact created a tail. Document honestly; NO tuning; NO OOS; ENSEMBLE-L1 is NOT preferred; single-phase Wed@00h remains the forward book. |

**ARITHMETIC-ANOMALY FLAG (Critic Condition A).** If maxDD clears its tier bar (SUCCESS or PARTIAL)
**but** headline Sharpe and/or 2×-cost Sharpe land **below their SOFT targets while still above their
HARD floors**, the tier **stands on the maxDD axis** — but raise an ARITHMETIC-ANOMALY FLAG. A
sub-band Sharpe is NOT a reason to demote the maxDD result; it is a signal that the realized
tranche-correlation / cost / alignment differs from the §2–§3 arithmetic (e.g. `rho_bar` far from the
predicted +0.88, a grid misalignment, or a cost surprise) — **investigate the mechanism, do not
downgrade the tail win.**

### 5.2 What "preferred design" means (IS-scoped)

SUCCESS/PARTIAL makes ENSEMBLE-L1 the track's **preferred construction on the maxDD/robustness axis**
— an IS design verdict, NOT a deployability claim. The ensemble's chief virtue is **honesty**: it
delivers the phase-agnostic +0.947-class level and a non-lucky maxDD, whereas single-phase Wed@00h's
+1.164 / −28.58% was a favorable, never-chosen draw (Sharpe rank 8/21; the −28.58% maxDD is
shallower than the phase mean −37.3% by luck).

### 5.3 FORWARD-RELATIONSHIP (recommendation logic pre-registered; USER decides, not this brief)

The running `PROTOCOL-L1-FORWARD` (T0 = **2026-07-15**, single Wed@00h L1 book) validates the
single-phase construction. **Switching the forward protocol to the ensemble is a CONSTRUCTION CHANGE**
(new T0, new protocol version) — and the **sibling-forward ban means one book must be CHOSEN, not both
run.** This is a **USER decision to be taken after this exploration's verdict**, never an automatic
action here. Pre-registered recommendation logic (the exact logic I will apply when I present the
verdict — frozen now so it is not tailored to the outcome):

1. **SUCCESS (HARD-all + maxDD ≤ −30%):** **RECOMMEND the user REPLACE single-phase Wed@00h with
   ENSEMBLE-L1 as the forward book.** Rationale: the ensemble is the phase-honest, non-cherry-picked
   construction — it forfeits the lucky +1.164 for the true +0.947-class level AND a diversified maxDD
   that beat the single-phase phase-mean tail. **Timing is ideal: as of 2026-07-10, T0 (2026-07-15)
   has not started, so ~zero forward data is forfeited by switching now** — this is the cleanest
   possible moment to choose the construction. Mechanics: new T0 on the next valid weekly boundary,
   protocol version bump; the ensemble's 21-phase forward diagnostic collapses to "the book IS the
   phase-average," so the M-phase contradiction gate is reframed (informational note for whoever
   authors the new protocol — NOT executed here).
2. **PARTIAL (HARD-all, maxDD in (−35%, −30%]):** **PRESENT BOTH with the trade-off; LEAN ensemble.**
   Single-phase Wed@00h carries a known favorable-draw level-inflation but is already pre-registered;
   ENSEMBLE-L1 is phase-honest but its maxDD only matches the phase mean (didn't beat the best phase).
   I lean ensemble because it eliminates phase luck — the largest un-booked deflation vector (ADDENDUM
   2 F9, retro-/005) — but it is the user's call.
3. **FAIL via G-dd (falsifier):** **Do NOT switch.** Single-phase Wed@00h remains the forward book.
   Record that the phase-tail is irreducible via ensembling — a forward-validation caveat that the
   single-phase book carries a genuine phase-driven tail risk (FF-1 breach elevated, ADDENDUM 2).
4. **FAIL via a non-maxDD HARD gate:** localize; do NOT switch; ensemble not preferred.

**T0-timing decoupling (Critic Condition B — process integrity).** The T0 timing **MUST NOT pressure
the verdict.** If the /007 review is not complete by T0 (2026-07-15), that is fine — a recommended
switch simply lands at a later weekly boundary with a few days of single-phase forward data as prior.
**Verdict quality takes absolute precedence over beating T0; the switch decision is decoupled from the
verdict timing.** Item 1's "timing is ideal" is an opportunity, never a deadline — nothing about the
running clock may compress the /007 evaluation.

**Cross-cutting note (applies to ALL outcomes):** regardless of the switch decision, the ensemble's IS
maxDD is the **single most informative new number for sizing the forward maxDD expectation of EITHER
book.** A phase-honest ensemble maxDD (e.g. ≈ −28%) is a more trustworthy central estimate of the
construction's true drawdown than the single-phase −28.58% favorable draw — it INFORMS the forward
maxDD band even if the user keeps single-phase.

---

## Section 6 — Multiple-testing honesty (n_eff)

- **This is the track's 7th exploration.** The construction is **ONE pre-committed, selection-free
  ensemble** (equal-weight all-21). The 21 tranche ingredients were ALREADY observed and already
  counted: ADDENDUM 2 ruling 4 booked the sweep as **zero best-of-k inflation + 1 researcher-DOF
  bump → cumulative n_eff ≈ 16–22.**
- **Honest increment for /007:** the ensemble introduces **no best-of-k selection** (nothing is
  chosen; equal-weight is the one aggregation that selects nothing) and **no tuned parameter.** The
  only genuine DOF is "decide to build the ensemble + adopt equal-weight" → **+1 researcher-DOF.** The
  Sharpe LEVEL is mechanically determined by the already-counted sweep, so **no NEW Sharpe-selection
  risk** is added. The one genuinely new observable — the ensemble maxDD — is a **single pre-committed
  measurement**, not a search. **Cumulative n_eff ≈ 17–23.**
- **Haircut instruction for the Critic:** apply a DSR/deflation consistent with cumulative n_eff ≈
  17–23 to any Sharpe reported here. **BUT** this phase is **IS-only with NO OOS reveal**, so per the
  track's EXPLORATION-mode DSR convention the deflation is **informational only** — it does not gate
  the IS design-validation verdict; it sizes expectations for a FUTURE forward test. Note also that the
  ensemble Sharpe is **already phase-deflated by construction** (it is the phase mean, not the lucky
  draw), so the residual deflation on the ensemble is *smaller* than on the single-phase +1.164 — a
  point in the ensemble's favor, not against it.

---

## Section 7 — Engineer deliverables spec

**Script:** `analysis/portfolio/blind_exploration_007.py`. **Reuse VERBATIM — single source of truth,
no reimplementation, no drift:** `run_l1`, `run_v0`, `trim_panel` from `blind_paper_l1` (the SAME
functions the sweep used); `leg_attribution`, `monthly_table`, `bucket_agg` from
`blind_exploration_006`; `mania_months` / `MANIA_MONTHS_FROZEN` from `blind_mania_rule`; `slice_is`
from `blind_sanity_lowvol`; `_metrics`, `CostModel`, `PERIODS_PER_YEAR` from `blind_engine`;
`load_panel`, `OOS_CUTOFF_MS` from `blind_universe`. **IS hard-slice at the top** (`pis = slice_is(
load_panel())`; assert `pis.grid_ms.max() < OOS_CUTOFF_MS` — ABORT on any OOS leak).

**Ensemble construction (frozen, exact):**
1. For `p in range(21)`: `res_l1_p = run_l1(trim_panel(pis, p))` and `res_v0_p = run_v0(trim_panel(
   pis, p))`. Map each tranche's `rets` (and `turnover`, and the four `leg_attribution` components)
   onto the ORIGINAL `pis` grid by candle (trimmed index `j` ↔ original index `p+j`; **align by
   `grid_ms`, not array position**). Pre-first-fill NaNs stay NaN.
2. **Common warmup=63 slice.** Each tranche is warm+finite at original index `t` iff `(t − p) ≥ 63`
   and its mapped `rets[t]` is finite. The COMMON valid region begins at `t* = max_p(p + 63) = 83`;
   assert the common mask first-True index equals 83 (loud on any drift). All ensemble metrics are
   computed on `[t*, T)` (IS by construction).
3. **ENSEMBLE-L1 return** `= (1/21)·Σ_p mapped_rets_l1_p[t]` on the common slice; equity compounds on
   it. **V0-ENSEMBLE** identically from `res_v0_p`.
4. **2×-cost twin (analytic, exact, driftless — do NOT modify `run_l1`).** Weights are
   cost-independent, so the 2×-cost tranche return `= mapped_rets_p[t] − mapped_turnover_p[t]·
   cost_side` where `cost_side = (5.0 + 2.5)/1e4`. Ensemble the 21 doubled-cost streams identically.
   **Assert** this analytic 2× reproduces a `CostModel(10,5,True)` re-run on tranche 0 — tolerance
   **≤ 1e-15 ELEMENTWISE on the per-candle `rets`** (where the identity `rets_2x[t] = rets_1x[t] −
   turnover[t]·cost_side` is exact), and **~1e-12 on any RECOMPOUNDED quantity** (Sharpe / equity —
   float accumulation over ~5,700 candles). One spot re-run on tranche 0 is enough. **The Critic
   verified the analytic twin is EXACT for L1** (no vol-target / dd-brake / gross-scalar controls →
   target weights are cost-invariant → the inter-rebal drifted-weight equity ratio cancels the cost
   dependence), so **the full ≈84-backtest matrix is NOT needed: 21 L1 + 21 V0 tranche runs (1×) +
   their analytic 2× twins suffice.**

**Compute note:** 42 tranche backtests (21 L1 + 21 V0 at 1×) + analytic 2× twins (post-processing, no
extra runs). All on the IS slice — fast; no long-run flag needed. (The full 84-run matrix with explicit
2× re-runs is admissible but redundant — the analytic twin is verified exact for L1.)

**Parity guards (ABORT on fail):**
- **Tranche p=0 reproduces the frozen candidate:** `_metrics(res_l1_0, cost, warmup=63)["sharpe"] =
  +1.1638 ± 0.005`, `res_v0_0 = +0.9134 ± 0.005`, L1 maxDD −28.58% ± 1pp, turnover 50.1x ± 2.
- **Full-sweep reproduction:** all 21 tranches' `_metrics(warmup=63)` Sharpe/maxDD reproduce
  `paper-l1/phase_sweep_is.csv` row-for-row (±1e-6) — ties the ensemble script to the committed sweep.

**Required deliverables (report tables — NO verdicts, observations only):**
1. **Headline block:** ENSEMBLE-L1 Sharpe (honest cost, PPY=1095), 2×-cost Sharpe, vol, maxDD,
   turnover (ann one-way), ann return, monthly win rate, top-10-month concentration share.
2. **Per-year ensemble Sharpe** {2020,2021,2022,2023,2024,2025Q1}.
3. **CRASH bucket (20 market-defined months, §3.3 of /006)** and **MANIA bucket
   (`MANIA_MONTHS_FROZEN`, 13 months)** aggregates for ENSEMBLE-L1 AND V0-ENSEMBLE, each with
   **aggregate leg P&L** (long_px / short_px / net_fund) — leg components averaged across tranches then
   bucketed. Report the G-mania threshold = `mania(V0-ENSEMBLE) + 2.0pp` explicitly.
4. **Monthly table** for ENSEMBLE-L1 (compounded return + leg split per month) and **worst-10 months**.
5. **Tranche-correlation summary:** the 21×21 Pearson correlation matrix of tranche return streams on
   the common slice → report **mean off-diagonal pairwise correlation `rho_bar`** (+ min/max pair).
   This scores the §3 `rho_bar` prediction and the diversification-factor reasoning.
6. **Turnover verification:** report ensemble one-way turnover AND the derivation (‖ in §4), plus the
   disclosed no-netting conservative-bias statement.
7. **Gate scorecard:** all 14 gate lines (§4), each HARD/SOFT with pass/fail, and the resolved
   **SUCCESS / PARTIAL / FAIL** tier per §5.1. (Verdict rendering is the QR's Phase-7 job; the engineer
   reports the numbers + mechanical pass/fail only.)

**Leak / integrity discipline:** IS-slice + runtime OOS-seal assert at the top; all tranche runs on
front-trimmed IS panels (front-trim only — the OOS boundary is never touched, identical to
`blind_phase_sweep_006`); leg reconciliation `long_px+short_px+net_fund−tcost ≡ rets` asserted ≤ 1e-15
per tranche; the analytic-2× vs re-run agreement asserted on tranche 0. **Do NOT:** touch OOS, read any
baseline/CONFIRMATION artifact, touch `PROTOCOL-L1-FORWARD` or `paper-l1/` forward logs, change any
FROZEN L1 parameter, select or weight any phase unequally, or re-run/re-tune after seeing results. Hand
the report to the QR for Phase-7 IS evaluation. **There is no OOS reveal in this phase.**

---

**FROZEN.** The construction (equal-weight all-21-phase ensemble of the byte-frozen L1), the gate
thresholds, the V0-ENSEMBLE references, the §3 predictions, the §5 decision map, and the §5.3
forward-recommendation logic are locked as of 2026-07-10, pre-run. Any deviation is a new EXPLORATION.
