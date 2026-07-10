# PHASE7-007 — EXPLORATION-007 IS gate evaluation + FROZEN verdict (phase-ensemble L1)

**Date:** 2026-07-10. **IS Verdict: FAIL** (G-crash HARD breach; frozen §5.1 map governs).
**Construction: ENSEMBLE-L1** — the equal-weight (1/21) all-21-phase ensemble of the byte-frozen L1.
7 of 8 HARD gates pass with wide margins; **G-crash fails (+0.933%/mo < the frozen +1.55% floor)**, and
because SUCCESS and PARTIAL both require ALL 8 HARD gates, the frozen interpretation map lands in the
**FAIL tier**. No goalpost is moved; no gate is re-anchored on this window.

**This is an IS design-validation, NOT a deployability claim. There is no OOS reveal in this phase**
(the /005 base already burned the one-shot OOS look; `OOS_CUTOFF = 2025-03-24` sealed; `CONFIRMATION-005.md`
not read). Every number below is IS-only. Engineer scope was respected (observations only); this
document renders the gate verdict, the §5.1 tier, the adjudication, the prediction scoring, and the
frozen §5 actions.

**Adjudication headline (Critic REVIEW-007, adopted in full):** the FAIL is a **genuine FAIL of a
mis-specified (mis-anchored) gate, not a construction failure.** It explains the tier; it does not
overturn it. Crash defense is empirically intact at the ensemble level. Details in §2.

---

## 1. Gate scorecard for ENSEMBLE-L1 (frozen §4) → FAIL tier

Common warmup=63 slice, IS-only (`[83, 5725]`, 5643 candles, 2020-01-28 .. 2025-03-23), PPY=1095.

| # | Gate | Type | Threshold | ENSEMBLE-L1 observed | Verdict |
|---|---|---|---|---|---|
| G-years | per-year Sharpe all ≥ 0 | HARD | every year ≥ 0 | min-PY **+0.709** (2022) | **PASS** |
| **G-crash** | crash-bucket (20mo) mean | HARD | **≥ +1.55%/mo AND > 0** | **+0.933%/mo** | **FAIL** |
| G-mania | mania-bucket (13mo) mean | HARD | ≥ V0-ENS mania + 2.0pp = **+0.758%/mo** | **+4.535%/mo** | **PASS** |
| G-sharpe-floor | headline Sharpe | HARD | ≥ +0.60 | **+1.2826** | **PASS** |
| G-2xcost | 2×-cost Sharpe | HARD | ≥ +0.45 | **+1.0921** (ground-truth) | **PASS** |
| G-dd-floor | maxDD | HARD | ≥ −35% | **−18.59%** | **PASS** |
| G-turnover | turnover ann one-way | HARD | ≤ 100x | **50.3x** | **PASS** |
| G-worst-month | worst calendar month | HARD | ≥ −15.0% | **−8.17% @ 2021-11** | **PASS** |
| G-crash-win | crash win rate | SOFT | ≥ 55% | **70%** | PASS |
| G-crash-leg | crash aggregate short_px | SOFT | > 0 | **+1.204** | PASS |
| G-mania-worst | mania worst month | SOFT | better than V0-ENS mania worst | **−4.25% vs −10.23%** | PASS |
| G-sharpe-target | headline Sharpe | SOFT | ≥ +0.90 | **+1.2826** | PASS |
| G-2xcost-target | 2×-cost Sharpe | SOFT | ≥ +0.75 | **+1.0921** | PASS |
| G-dd-target | maxDD | SOFT | ≥ −30% | **−18.59%** | PASS |

**7/8 HARD pass; G-crash FAILS. All 6 SOFT pass.** Per the frozen §5.1 map, SUCCESS and PARTIAL each
require **ALL 8 HARD** gates. One HARD gate fails ⇒ **TIER = FAIL.** The tier is rendered against the
thresholds frozen in the brief before the run; the candidate is the pre-committed selection-free
ensemble, not a post-hoc pick. **No IS re-gate is admissible** (see §5b).

---

## 2. Adjudication — the nature of the failure (Critic REVIEW-007 caveat 2, carried in full)

**The FAIL is a MIS-ANCHORED-GATE failure, not a crash-defense collapse.** The gate-localized evidence:

1. **The +1.55% floor was anchored to a single-phase-inflated number.** It was calibrated as 60% of
   **single-phase Wed@00h V0 crash (+2.586%/mo)** — but the crash bucket is the 20 violent squeeze/
   capitulation months, i.e. **exactly the most phase-sensitive bucket** (ADDENDUM 2 dispersion
   evidence). The phase-honest crash level is far lower: the **V0-ENSEMBLE crash mean is +0.935%/mo**,
   so the single-phase +2.586% is **~2.76× the phase-honest level**, and the +1.55% floor sits at
   **~1.66× even the no-overlay V0-ENSEMBLE crash reference.** The decisive fact: **BOTH** ensembles
   land at ~+0.93% (V0-ENS +0.935%, ENS-L1 +0.933%) — the floor is **un-clearable by ANY 21-phase
   ensemble of this construction**, overlay or not. That is the signature of a floor calibrated to a
   single-phase draw, not a floor the overlay failed to clear.

2. **On the metric the floor was designed to protect, the ensemble passes cleanly.** G-crash's design
   intent is "does the overlay preserve crash defense?" At the ensemble level the C1+C2 overlay is
   **crash-NEUTRAL**: ENS-L1 crash **+0.933% ≈ V0-ENS +0.935%**, the short leg remains the crash friend
   (**short_px +1.204 > 0**), and the crash **win rate is 70%** — identical to V0-ENS. The overlay
   removed nothing from crash defense; the construction is **not disqualified on crash merits.**

3. **The contract carried an anchoring asymmetry that BOTH pre-flights missed.** G-mania was
   correctly re-anchored to the **V0-ENSEMBLE** reference (relative, ensemble-vs-ensemble); G-crash was
   left on the **single-phase-derived absolute floor**. That asymmetry is the defect that caused the
   FAIL. The pre-flight Critic and I both missed it. The Critic owns its share (REVIEW-007 §5.2); I own
   the QR share below.

**The FAIL therefore indicts the gate specification and the ex-ante crash model — not the ensemble's
crash defense.** The tier stands (frozen map, no re-anchoring on this window); the *reason* is
localized here so no downstream reader mis-reads it as a crash-alpha collapse.

### 2.1 QR-owned calibration errors (my share; ledgered REVIEW-007 F4)

I own two independent calibration errors, both disclosed without hedging:

- **(E1) The `rho_bar` conceptual error — holdings-overlap ≠ return-stream correlation.** My §2/§3
  reasoning ("near-identical holdings shifted ≤ 6.7 days ⇒ return streams ~0.88-correlated") conflated
  *portfolio-holdings overlap* with *8h-return-stream correlation*. On this fixed-share engine the
  carried shares drift and re-normalize between rebals, and the staggered rebal timing means two
  distant-phase books rarely hold the same freshly-rebalanced portfolio simultaneously — so the return
  streams decorrelate far more than holdings overlap suggests. Observed **`rho_bar` = +0.5245** (max
  pairwise only +0.84), not the predicted +0.88 [+0.80, +0.94]. This was the ROOT prediction miss and
  it cascaded into four *favorable* misses (§3). The error is conceptual, not arithmetic; the fix is to
  reason about return-stream correlation directly (or measure it), never infer it from holdings.
- **(E2) The crash-level over-estimate — independent of E1.** I predicted ensemble crash **+1.7%/mo
  [+1.3, +2.1]**; observed **+0.933%**. I anchored the prediction on the single-phase Wed@00h L1 crash
  (+1.754%) and failed to anticipate that staggering averages the crash bucket **down** exactly like
  every other bucket — the single-phase crash number was itself a favorable phase draw. Had I modeled
  the crash bucket as phase-honest (≈ V0-ENSEMBLE +0.93%) rather than single-phase, I would have (a)
  predicted the crash mean correctly AND (b) flagged in the brief that a single-phase-derived absolute
  +1.55% floor is un-clearable by any ensemble — catching the anchoring asymmetry before the run. **E2
  is the QR-side root of the mis-anchored gate.**

Both errors are calibration-quality gaps, not discipline failures: the bands were falsifiable and
pre-registered, and every miss is diagnosed here. But they are real, and they are on the record.

---

## 3. Prediction scorecard (frozen §3) — 4 HIT / 6 MISS

| quantity | point | band | observed | HIT/MISS |
|---|---|---|---|---|
| rho_bar | +0.88 | [+0.80, +0.94] | **+0.5245** | **MISS** (root) |
| Ensemble Sharpe | +0.98 | [+0.90, +1.08] | **+1.2826** | **MISS** (favorable) |
| Ensemble vol (÷ single-phase) | 0.94× | [0.88×, 0.98×] | **0.737×** | **MISS** (favorable) |
| Ensemble maxDD | −28% | [−22%, −36%] | **−18.59%** | **MISS** (favorable) |
| Ensemble 2×-cost Sharpe | +0.86 | [+0.76, +0.96] | **+1.0921** | **MISS** (favorable) |
| Ensemble turnover | +50x | [+48x, +55x] | **50.3x** | **HIT** |
| Ensemble crash mean (20mo) | +1.7% | [+1.3%, +2.1%] | **+0.933%** | **MISS** (adverse — the consequential one) |
| Ensemble mania mean (13mo) | +4.8% | [+3.8%, +5.8%] | **+4.535%** | **HIT** |
| Ensemble worst month | −11% | [−8%, −14%] | **−8.17%** | **HIT** |
| Min per-year Sharpe | +0.2 | all years ≥ 0 | **+0.709** | **HIT** |

**The `rho_bar` cascade.** One conceptual miss (rho_bar 0.52 not 0.88) drove five of the six misses:
the diversification factor `sqrt(21/(1+20·rho_bar))` came in at **1.35, not the assumed ~1.05**, which
lifted the ensemble Sharpe well above its band, cut the vol to 0.737×, and clipped the maxDD below its
band (all *favorable* surprises). The **sixth miss — crash +0.933% vs +1.7%** — is **independent of
rho_bar** (E2 above) and is the one that cost the phase its tier.

**Known-arithmetic vs discovered-diversification decomposition of the +1.28 Sharpe (my §2a
over-claim, corrected).** My §2 declared "the ensemble Sharpe LEVEL is known ex-ante." That was
**partly wrong**: the *mean return* was known arithmetic (= the phase mean), but the *Sharpe's
denominator (vol via rho_bar) was a genuine unknown* and the real discovery. The engineer's TABLE 9
confirms the arithmetic: phase-mean Sharpe **+0.947 × div-factor 1.3519 = +1.281 ≈ observed +1.2826.**
So of the +1.28: **~74% (+0.947) is known arithmetic** (the phase mean, already in the sweep) and
**~26% (+0.335) is the discovered diversification benefit** (the vol reduction from the
lower-than-expected correlation). My honesty framing was directionally right — a headline near the
phase mean proves arithmetic, not edge — but I under-credited the diversification denominator as a real,
unknown-ex-ante discovery. Corrected for the record.

---

## 4. Exploratory findings that STAND (descriptive; explicitly NOT gate-certified)

These are honest IS observations from the frozen pass. **None is gate-validated** — the phase is FAIL,
the IS crash gate is spent (§5b), and no OOS was touched. They are carried as descriptive evidence, not
claims:

1. **The phase-tail is EMPIRICALLY time-diversifiable — F7 of ADDENDUM 2 resolved.** ENSEMBLE-L1 maxDD
   **−18.59%** is **shallower than EVERY single-phase tranche** (best single phase −21.31%, phase mean
   −37.3%, worst −70.4%) — **+18.71pp shallower than the mean tranche maxDD.** At the ensemble trough
   (2022-02), **0/21 tranche troughs coincide**; the deep-DD phases (p13–p16, −57% to −70%) all trough
   in 2024-10/2024-08 and are offset there by phases that don't crater. This is textbook staggered-entry
   time-diversification: the squeeze that individually kills a phase is diversified away in the
   ensemble. The ADDENDUM 2 open question ("do the 7/21 tail phases drag the ensemble through the floor,
   or does entry-point diversification clip the tail?") is answered — **the tail is clipped.**
2. **The C1+C2 overlay mechanism is preserved at the ensemble level.** Mania bucket **−1.242% → +4.535%**
   (win 38% → 77%; short_px −2.313 → −1.462 — the squeeze cut is visible); crash short leg intact
   (short_px +1.204). The overlay does at ensemble scale exactly what DIAGNOSTIC-003 / RISK-006
   designed it to do at single-phase scale.
3. **All six IS part-years are positive** (min **+0.709** @ 2022), whereas the no-overlay V0-ENSEMBLE
   has a negative 2021 (−0.35) and near-zero 2023 (+0.01). The overlay converts a phase-honest base with
   a losing year into an all-years-positive book.
4. **The phase-honest level is +1.28** — above both the phase mean (+0.947) and the single-phase Wed@00h
   lucky draw (+1.164), driven by the discovered diversification denominator (§3).

---

## 5. Actions (frozen §5 map + Critic REVIEW-007 caveat 3)

### 5a. NO switch — the single-phase Wed@00h forward book continues (frozen §5.3 binds the action)

G-crash is a non-maxDD HARD gate, so the FAIL routes through frozen **§5.3 item 4: "localize; do NOT
switch; ensemble not preferred."** **A FAILED phase does not promote its construction.** The
single-phase Wed@00h L1 forward book continues **unchanged** under `PROTOCOL-L1-FORWARD` (T0 =
2026-07-15). **Correction to the frozen reason (Critic caveat 3):** §5.3 item 4's implicit
localization ("crash alpha lost in aggregation") is **wrong per §2** — crash defense is intact; the
FAIL is a mis-anchored gate. The **action stands** (no switch), but the **reason is corrected** so the
record is honest. Nothing in `PROTOCOL-L1-FORWARD` is touched by this document.

### 5b. The IS crash gate for this construction/window is SPENT — no /008 IS re-gate

All ensemble numbers are now revealed. A "corrected-floor /008" that re-runs the ensemble on the SAME
IS window against a re-anchored crash gate would be **post-hoc gate-fitting** on a burned window —
inadmissible. **The IS crash gate for ENSEMBLE-L1 on this window is spent; it failed.** Do not re-gate
it in-sample. (This is the same discipline that governs OOS: a revealed number cannot re-adjudicate its
own gate.)

### 5c. SEPARATE, DECOUPLED user decision — a fresh forward pre-registration for ENSEMBLE-L1

Decoupled from /007's frozen logic (which only ever bound the no-switch action), the ensemble is
presented to the **user** as a candidate for a **NEW, freshly pre-registered FORWARD protocol** on
**genuinely unseen data**, with a **crash-defense-PRESERVED gate anchored to PRINCIPLE, not the
revealed number**:

> **Forward crash gate (principle-anchored):** forward crash-bucket mean **> 0** AND forward
> crash-bucket **short_px > 0** AND forward crash mean **≥ forward V0-ENSEMBLE crash mean**
> (apples-to-apples, ensemble-vs-ensemble). No absolute number inherited from this IS window.

**Sibling-forward ban.** If the user opts for the ensemble forward test, **ONE forward book must be
chosen** — the ensemble **replaces** single-phase Wed@00h under a **new T0 / new protocol version**.
**Never both** run in parallel.

**The trade-off, stated honestly:**
- **Keep single-phase Wed@00h:** validates the **exact /006 candidate** that survived REVIEW-006 — but
  it carries the **phase-lottery maxDD risk** (its −28.58% was a favorable draw; phase mean −37.3%,
  7/21 breach −35%; the FF-1 −35% forward floor is at elevated, plausibly phase-driven breach risk per
  ADDENDUM 2 F7/F8). Forward-validating a construction whose headline is known to be a lucky draw is
  low-information on the level and the tail.
- **Switch to ENSEMBLE-L1 (fresh forward pre-registration):** the **phase-honest construction with the
  empirically-clipped tail** (−18.59%, shallower than every tranche; phase luck structurally removed) —
  but its **only pre-registered IS gate outcome was FAIL-on-a-mis-anchored-gate**, so a **fresh forward
  pre-registration on unseen data is the only clean validation path**, and forward tranche correlation
  could rise in stress (rho_bar climbing from 0.52 would shrink the diversification benefit exactly when
  it is needed). Honest forward expectation **~+0.70–0.95, central ~+0.80** (above single-phase L1's
  +0.55–0.80; below the IS +1.28).

**QR RECOMMENDATION (clearly labeled — the decision is the user's).** I **recommend the user authorize
a fresh forward pre-registration for ENSEMBLE-L1 to replace single-phase Wed@00h**, with the
principle-anchored crash-defense gate above and a new T0/protocol version. Reasoning:
1. **The axis that matters most for this book is drawdown robustness, and the ensemble empirically wins
   it.** This entire track's ADDENDUM-2 finding was phase-tail fragility (F7/F9); the ensemble
   *resolves* it (tail clipped to −18.59%, 0/21 trough coincidence, phase luck removed — the single
   largest un-booked deflation vector). The single-phase book forward-validates a construction whose
   +1.164/−28.58% is a known favorable phase draw.
2. **The /007 FAIL does not indict the ensemble's crash defense** (§2): it passes the
   crash-defense-preserved principle already (+0.933% > 0, short_px +1.204 > 0, ≈ V0-ENS +0.935%). The
   FAIL was a contract-anchoring defect, now understood — not a mechanism failure.
3. **A principle-anchored forward gate on unseen data is the clean validation the ensemble needs** and
   the single-phase book cannot provide for it.
4. **Timing is favorable but NOT decisive** (brief §5.3 T0-decoupling clause): T0 (2026-07-15) has not
   started, so ~zero forward data is forfeited by switching now — but this is an opportunity, never a
   deadline; the user should weigh construction merit, not the clock.

**Honest counter-weight the user must price in:** the ensemble is a NEW construction requiring full
forward re-validation from scratch, and its forward Sharpe is unproven (correlation-regime risk). A
risk-averse choice to keep validating the exact, REVIEW-006-blessed single-phase candidate — accepting
its phase-lottery tail risk as a known, disclosed cost — is defensible. **My recommendation is the
ensemble switch; the call is the user's.**

---

## 6. Corrected technical record (Critic REVIEW-007 caveat 6) — the analytic 2×-cost twin is NOT exact

For any future brief on this **fixed-share engine**, inherit this correction:

**The brief §7 / REVIEW-007-preflight premise that `rets_2x[t] = rets_1x[t] − turnover[t]·cost_side`
is EXACT elementwise (≤ 1e-15) is WRONG.** The identity holds **only at cost-bearing rebal candles**
(tranche-0 error there = 0.0e+00). **Between rebals it drifts:** the carried fixed shares are
re-normalized by the running equity — the drifted effective weight `w_eff = shares·price/E` scales by
the equity ratio `E_rebal/E[k−1]`, and `E[k−1]` contains the rebal candle's own cost-bearing return, so
**the cost does NOT cancel.** Measured: tranche-0 elementwise max deviation **7.13e-05** (mean 3.9e-6);
ensemble 2×-cost Sharpe analytic-vs-ground-truth deviation **−0.00009** (negligible, the G-2xcost read
is unaffected).

**Resolution used (correct):** the engineer reported the **GROUND-TRUTH re-run matrix (21 L1@2× + 21
V0@2×, `CostModel(10,5)`)** as the authoritative 2×-cost number (**+1.0921**); the analytic twin was
carried only as a cross-check. The engineer's handling was exemplary. **Rule for future briefs:
cost-independence claims on this fixed-share engine must be verified EMPIRICALLY (ground-truth diff),
never by analytic argument alone.** (I asserted the analytic exactness in the /007 brief §7 on the
Critic's preflight endorsement; both were wrong — corrected here.)

---

## FROZEN VERDICT: FAIL (G-crash). ENSEMBLE-L1 clears 7 of 8 HARD gates + all 6 SOFT gates by wide
margins, but its crash-bucket mean **+0.933%/mo** falls below the frozen **+1.55%/mo** HARD floor, and
the frozen §5.1 map (SUCCESS/PARTIAL both require ALL 8 HARD) lands in the **FAIL tier** with no
re-anchoring on this window. **The failure is adjudicated as a MIS-ANCHORED-GATE failure, not a
crash-defense collapse:** the +1.55% floor was 60% of a single-phase V0 crash draw (~2.76× the
phase-honest level), un-clearable by ANY 21-phase ensemble (V0-ENSEMBLE crash is itself +0.935%), while
the overlay is crash-neutral (ENS-L1 +0.933% ≈ V0-ENS +0.935%, short_px +1.204 > 0, 70% win) — an
anchoring asymmetry (G-mania re-anchored to V0-ENSEMBLE, G-crash left absolute) that both pre-flights
missed and whose QR-side root is my crash-level over-estimate (E2). Exploratory findings stand but are
NOT gate-certified: the phase-tail is empirically time-diversifiable (maxDD −18.59%, shallower than
every tranche, 0/21 trough coincidence), the overlay mechanism is preserved at ensemble level, all IS
years are positive (min +0.709), and the phase-honest level is +1.28 (~74% known arithmetic + ~26%
discovered diversification). **Actions:** (a) NO switch — the single-phase Wed@00h L1 forward book
continues unchanged under PROTOCOL-L1-FORWARD (T0 2026-07-15), the §5.3-item-4 action upheld with its
"crash alpha lost" reason corrected; (b) the IS crash gate for this construction/window is SPENT — no
/008 IS re-gate is admissible; (c) SEPARATELY and decoupled, a user decision is presented — whether to
pre-register a NEW forward protocol for ENSEMBLE-L1 with a principle-anchored crash-defense-preserved
gate on genuinely unseen data, one forward book only (ensemble replaces single-phase, new T0/version),
which I **recommend** on drawdown-robustness grounds while pricing the honest counter-weight that the
ensemble is a new construction needing full forward re-validation. No OOS was touched.
