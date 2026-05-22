# iter-v3/090 — Cycle 3 #9 EXPLORATION — the GROSS-SIGNAL-STRENGTHENING cross-sectional iteration: downside-risk feature expansion / FEATURE-EXPANSION-FALSIFIED / Critic Phase-7.5 OVERALL=BLOCK

**Date**: 2026-05-17
**Type**: EXPLORATION (cycle 3 slot #9 of 10) — gross-signal-strengthening build on the RETAINED /088 cross-sectional `LGBMRanker` architecture + the /089 cost-aware construction. Single-axis: a feature expansion — 2 engineered downside-risk features (`xs_sortino_mom_12`, `xs_downbeta_50`) appended to the cross-sectional ranker's feature set (13 → 15). EXPLORATION-mode single-seed (seed=42), `ensemble_size=1`, `--n-trials 35`, 22-symbol panel, wall-clock 0h 20m 39s.
**Verdict**: **OVERALL = BLOCK** — Critic Phase-7.5 review (`briefs-v3/iteration_v3-090/review.md`, FINAL `95065ee`). The BLOCK is **FINAL** — /090 is recorded as a BLOCKED, NO-MERGE iteration; the Critic was NOT re-run.
**Classification**: **FEATURE-EXPANSION-FALSIFIED** (brief Section 8.2) — filed on the *corrected* gross-Sharpe recompute (this diary, Section 3). The Critic's expectation (review §"My read on the Section 8 classification") and the recomputed F3 result converge: 8.2 is canonical.
**Decision**: **NO-MERGE.** The 2 downside-risk features are DROPPED. The cross-sectional architecture + `cross_sectional.py` infrastructure + the /089 cost-aware construction are RETAINED (the architecture is not falsified — only the /090 feature additions are).
**BASELINE_V3.md**: **UNCHANGED** — canonical /059 metrics (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791), tag `v0.v3-059`. An EXPLORATION never updates the baseline regardless of classification; a BLOCKED EXPLORATION certainly does not.
**Branch**: `iteration-v3/090`

---

## 1. Why this iteration is BLOCKED, not merely NO-MERGE

iter-v3/090 would be NO-MERGE on its own merits regardless — it is an EXPLORATION on an architecture that has not beaten breakeven, and an EXPLORATION carries no merge ingredient. But the Critic's verdict is **OVERALL = BLOCK**, a strictly stronger negative finding, and it must be recorded as such. The distinction is not pedantic:

- **NO-MERGE** = the result did not clear the merge bar. A clean negative.
- **BLOCK** = a *process-integrity defect* in the iteration's load-bearing evidence. The classification cannot be *filed* on the artifacts as delivered.

The /090 *run* is methodologically clean — the Critic's Checks 1-2 and 4-12 all PASS (look-ahead audited, embargo `XS_REQUIRED_GAP = 88` correct, the 2 new features orthogonal to the existing stack, single-axis claim holds, code faithfully implements the brief). Check 3 (DSR/PSR/PBO) is an informational EXPLORATION-mode FAIL, non-blocking per `feedback_v3_dsr_mode_artifact.md`.

The BLOCK is **Check 8** — the engineering report's central diagnostic is defective. The report's load-bearing finding — *"/090 OOS gross monthly Sharpe FELL from /089's +0.5947 to +0.5398; the gross signal was NOT strengthened"* — is wrong on two counts:

1. **The /089 anchor +0.5947 is wrong.** /089's documented OOS gross monthly Sharpe is **+0.1717**, stated in three independent merged /089 artifacts (the /089 engineering report, the /089 Critic review, `diary-v3/iteration_v3-089.md`) and in the /090 brief itself (Section 1, Section 4.1, falsifier F3). The /090 engineering report's +0.5947 contradicts the very brief it implements.
2. **+0.5947 is mathematically impossible for /089's OOS book.** The Critic showed it would require `corr(net, fee) ≈ −6.8`. Both reports' gross monthly Sharpe figures (+0.1717, +0.5947, +0.5398, +0.2675, +0.3204) are QE hand-computations on a non-per-month basis with no reproducible derivation — the engineering report's own Anomaly Note 2 admits "different monthly aggregation."

The Section 8 classification turns on falsifier F3 — *"/090 OOS gross monthly Sharpe ≤ /089's +0.1717"* — and that input was corrupt. **A methodology defect in a classification-driving number is OVERALL=BLOCK** regardless of the (likely-correct) negative direction. The honest closeout is: recompute the number correctly, re-evaluate F3, file the classification on the corrected evidence, and record the process defect so it does not recur.

---

## 2. TASK 1 — the corrected gross monthly Sharpe recompute (Critic Rec #2)

Committed analysis script `analysis/iteration_v3-090/gross_sharpe_recompute.py` (output saved to `gross_sharpe_recompute_output.txt`). Pure analysis on the committed trades CSVs — no runner/`src` change, no backtest re-run.

**Method** (identical for /089 and /090, IS and OOS): bucket each trade into its calendar month by `open_time` (the trades CSV carries no other timestamp; this is the field `monthly_pnl.csv` is keyed on); sum the PnL column per calendar month → monthly series → Sharpe = `mean/std`, sample std (`ddof=1`), **no annualization**.

**Validation step first** (this is what proves the basis is correct): the recomputed *net* monthly series and net monthly Sharpe must reproduce `monthly_pnl.csv` and `comparison.csv`. They do — to machine precision:

| iter | split | net Sharpe (comparison.csv) | net Sharpe (recomputed) | monthly_pnl.csv series | net match |
|---|---|---:|---:|---|:--|
| /089 | IS  | −0.195953 | −0.195953 | max\|Δ\| 4.7e-15 | MATCH |
| /089 | OOS | −0.098453 | −0.098453 | max\|Δ\| 3.8e-15 | MATCH |
| /090 | IS  | −0.230458 | −0.230458 | max\|Δ\| 2.8e-15 | MATCH |
| /090 | OOS | −0.077043 | −0.077043 | max\|Δ\| 4.0e-15 | MATCH |

All four net validations reproduce the runner artifacts exactly. The per-calendar-month aggregation on `open_time` **is** the basis the runner's net monthly Sharpe uses. The recompute is therefore on the correct, like-for-like basis.

**The authoritative gross monthly Sharpe** (same method, `gross_pnl` column):

| iter | split | net monthly Sharpe (comparison.csv) | net monthly Sharpe (recomputed) | **gross monthly Sharpe (recomputed)** |
|---|---|---:|---:|---:|
| /089 | IS  | −0.195953 | −0.195953 | **+0.092485** |
| /089 | OOS | −0.098453 | −0.098453 | **+0.171676** |
| /090 | IS  | −0.230458 | −0.230458 | **+0.077216** |
| /090 | OOS | −0.077043 | −0.077043 | **+0.155841** |

**Findings.**
- /089 OOS gross monthly Sharpe recomputes to **+0.171676** — it **reproduces the documented +0.1717 to 4 decimal places**. The merged /089 record is correct; the /090 engineering report's +0.5947 is confirmed wrong (and the Critic's impossibility proof confirmed).
- /089 IS gross monthly Sharpe recomputes to **+0.092485** — reproduces /089's documented IS gross +0.0925. Both /089 figures are vindicated; the defect is entirely in the /090 report's hand-computation.
- /090 OOS gross monthly Sharpe is **+0.155841** — *not* the report's +0.5398. The report's gross figures are confirmed to be on a wrong (non-per-month) basis: /090 IS recomputes to +0.0772 vs the report's +0.2675; /090 OOS to +0.1558 vs +0.5398.
- The corrected, like-for-like comparison: **/090 OOS gross monthly Sharpe +0.1558 vs /089's +0.1717 — a DROP of −0.0159.** The *direction* the engineering report claimed (gross signal fell) is correct; the *magnitude and both anchor numbers* were wrong.

---

## 3. TASK 2 — falsifier F3 re-evaluation, and TASK 3 — the Section 8 classification

### 3.1 — F3 re-evaluation (corrected inputs)

Brief Section 4.3 falsifier **F3** (exact text): *"OOS gross monthly Sharpe ≤ the /089 book's +0.1717: the feature expansion did NOT strengthen the gross signal OOS — the central /090 hypothesis is falsified."*

- /089 OOS gross monthly Sharpe (correct anchor): **+0.1717** (documented; recompute confirms +0.171676).
- /090 OOS gross monthly Sharpe (corrected recompute): **+0.155841**.
- **+0.155841 ≤ +0.1717 → F3 FIRES.**

The verdict is robust to which /089 anchor is used: F3 fires against the documented +0.1717 *and* against the recomputed +0.171676 — they are identical to 4 decimals. The corrupt +0.5947 anchor would have inverted the test (it would have made the comparison +0.5398 vs +0.5947, still "fell" by luck of the sign — the engineering report reached the right *direction* on two wrong numbers). The corrected evaluation puts F3-fires on a sound footing: **the 2 downside-risk features did not strengthen the OOS gross signal — they weakened it by −0.0159 gross monthly Sharpe.** The central /090 hypothesis is falsified.

F1 (OOS rank-IC ≤ 0) does NOT fire — OOS rank-IC +0.0358 > 0. F2 (IS turnover > 0.138) does NOT fire — IS turnover/bar 0.1177 ≤ 0.138. F4 (OOS net monthly Sharpe ≤ /089's −0.0985) does NOT fire — /090 OOS net −0.0770 > −0.0985. F5 (single symbol > 50% OOS PnL) does NOT fire — max OOS concentration FILUSDT 11.38%.

### 3.2 — Section 8 classification: FEATURE-EXPANSION-FALSIFIED (8.2)

The brief Section 8 taxonomy runs in disjunctive precedence — first match canonical: 8.1 SUSPICIOUS → 8.2 FEATURE-EXPANSION-FALSIFIED → 8.3 VALIDATED-PROMISING → 8.4 PARTIAL → 8.5 NULL.

- **8.1 SUSPICIOUS — does NOT fire.** (a) OOS net / IS net Sharpe = −0.0770 / −0.2305 = +0.334 — not > 3.0 (two negatives; not the OOS-soars-on-flat-IS divergence). (b) OOS rank-IC +0.0358 is *weaker* than the model's IS-train rank-IC — the opposite of the SUSPICIOUS pattern. (c) OOS gross monthly Sharpe +0.1558 is not ≥ 3× /089's +0.1717 — it is *below* it. None of the three SUSPICIOUS conditions fire.
- **8.2 FEATURE-EXPANSION-FALSIFIED — FIRES, and is canonical.** 8.2 fires if (NOT SUSPICIOUS) AND (F2 OR F3 OR F4). **F3 fires** (the corrected recompute: +0.1558 ≤ +0.1717). The disjunction is satisfied. The feature expansion did not strengthen the OOS gross signal → the /090 gross-signal-strengthening hypothesis is falsified for the cycle. **NO-MERGE.** The 2 features are dropped; the cross-sectional architecture and `cross_sectional.py` infrastructure are RETAINED (8.2 does not falsify the architecture — the /088/089 OOS rank-IC stands; only the /090 feature additions are falsified).
- **8.3 / 8.4** are not reached (8.2 matched first under disjunctive precedence; and both 8.3 and 8.4 require `OOS gross monthly Sharpe > /089's +0.1717`, which is false).

### 3.3 — Corroborating negative signals (independent of the gross-Sharpe number)

The 8.2 verdict does not rest on F3 alone — every other diagnostic agrees the feature expansion did not transfer:

- **`frac_positive_paths` (CPCV)**: 0.356 (/089) → **0.200** (/090) — 9 of 45 IS CPCV paths positive, down from 16/45. A degraded IS gross signal.
- **IS net monthly Sharpe**: −0.1960 (/089) → **−0.2305** (/090) — IS net *worsened* by −0.0345.
- **IS gross monthly Sharpe** (recomputed): +0.0925 (/089) → **+0.0772** (/090) — IS gross *also* fell.
- **OOS rank-IC delta**: +0.0079 (/090 +0.0358 vs /089 +0.0279) — positive but *swamped by the OOS rank-IC std of ±0.34*; statistically indistinguishable from zero.
- **OOS net monthly Sharpe**: −0.0985 → −0.0770 (+0.0215). This is the *only* metric that moved in /090's favour — and it is fee-noise within fee-dominated books. The mechanism (engineering report, confirmed): the IS gross signal *dropped*, compressing the IS/OOS gross gap; the headline OOS net "improvement" is not a gross-signal gain.

Every signal points the same way: the 2 downside-risk features did not strengthen the cross-sectional gross signal — IS *or* OOS. FEATURE-EXPANSION-FALSIFIED is the honest, well-corroborated classification.

---

## 4. Phase 7 failure-mode-prediction check (brief Section 7)

The brief Section 7 pre-registered the outcome distribution. Did /090 fail the way the brief predicted?

- **≈45% modal** — "feature expansion materially improves the OOS book; OOS gross monthly Sharpe lifts toward [+0.20, +0.30]; OOS net toward [−0.10, +0.20], plausibly net-positive; sub-floor."
- **≈20% — F3/F4 fire**: "the feature expansion does NOT strengthen the gross signal OOS (OOS gross monthly Sharpe ≤ +0.1717) ... the IS composite IC-IR lift did not transfer."
- **≈20%** net-positive clearly; **≈10%** marginal-mechanical; **≈5%** full success.

**The realized outcome IS the brief's ≈20% F3 path** — *"the IS composite IC-IR lift did not transfer OOS."* The brief named this scenario precisely and even named the dominant mechanism: *"most likely the downside-risk features' contribution was IS-regime-specific, or the trained `LGBMRanker` at the EXPLORATION single-seed allocated colsample picks to the new features in a way that did not generalise (the residual iter-v3/070 risk, even after the redundancy cut)."*

The /090 result is *worse* than even that prediction in one respect: the brief's F3 path assumed the IS composite IC-IR lift was real and merely failed to transfer. The recompute shows the IS *gross monthly Sharpe* itself fell (+0.0925 → +0.0772) and `frac_positive_paths` dropped 0.356 → 0.200 — the trained `LGBMRanker` on the 15-feature stack produced a *weaker* IS gross book than the 13-feature stack. The model-free composite-IC-IR EDA (+9.6%) and the trained-model gross book diverged in sign. This is the iter-v3/070 colsample-dilution mechanism operating as the brief feared — and it is a documented v3 lesson: `feedback_v3_inert_features_at_higher_budget.md` (INERT features at higher Optuna budget *actively harm* OOS). `xs_downbeta_50` had a near-zero IS rank-IC (−0.005, rank ~18/22) — close to INERT — and at `n_trials=35` the larger search space let Optuna overfit IS noise including the weak 15th feature.

**Calibration verdict: the brief's failure-mode prediction was correct.** Section 7 named the F3 path, weighted it at ≈20%, and identified the exact mechanism (colsample dilution / non-transferring IS contribution). The brief did not over-claim — it weighted full success at only ≈5% and stated plainly even the modal success would be sub-floor. The one honest miss: the brief's modal case (≈45%) assumed the feature expansion would at least *not hurt* IS; in fact IS gross fell too. The brief's Section 7 was well-calibrated on the *failure* path that materialized.

The process defect that triggered the BLOCK is **not** a brief-calibration miss — it is an *engineering-report* defect (a hand-computed metric on the wrong basis). The brief itself anchored correctly on +0.1717 throughout. The defect was introduced in Phase 6.

---

## 5. The honest trajectory of the cross-sectional line

The catalog and the /088/089 diaries describe the cross-sectional line as "v3's most sustained positive trajectory." That framing must now be stated honestly. The line is **two mechanical gains plus one failed edge attempt — not an unbroken ascent.**

| Iter | OOS net monthly Sharpe | Δ vs prior | What the lift was |
|---|---:|---:|---|
| /088 | −0.5418 | — | cross-sectional ranker stood up; OOS rank-IC +0.043 transfers (genuine signal), but the BOOK loses |
| /089 | −0.0985 | **+0.4433** | **MECHANICAL** — a sign fix (/088 longed the wrong tercile) + a turnover cut (quintile + 3-bar holds + no-trade band). Removing *drag*, not adding *edge*. |
| /090 | −0.0770 | +0.0215 | the **first genuine attempt to ADD gross edge** (a researched, multivariate-tested, redundancy-cut feature expansion) — **and it did not transfer.** The +0.0215 is fee-noise; the gross signal *fell* (OOS gross +0.1717 → +0.1558; IS gross +0.0925 → +0.0772). |

The honest read:

1. **/089's +0.44 lift was a one-time mechanical correction.** A sign error and a turnover excess are *bugs*. Fixing them recovers performance that was always there in the signal — it does not create new edge. There is no second sign error to fix and no further turnover headroom (the /089 Critic Rec #2 established that pushing the construction harder *destroys* the gross signal — EDA E3 shows gross going negative at hold ≥ 3).
2. **/090 was the first real test of whether the cross-sectional gross signal can be *grown*. It failed.** A properly-researched, IS-EDA-selected, iter-v3/070-disciplined feature expansion did not strengthen the OOS gross signal — and weakened the IS gross signal. This is the data point the /089 closeout and the /090 Critic both flagged as the one that "should force a hard look."
3. **The cross-sectional gross signal is genuinely thin and not responding to feature work.** OOS gross monthly Sharpe sits at +0.16–0.17. The OOS rank-IC is +0.03–0.04 — real (it transfers) but faint. In the current **22-altcoin / ~1-day-hold / momentum-rank** construction the gross signal is too thin to monetize at the current cost structure (OOS fees/gross ≈ 1.58×). /090 establishes that feature expansion is not the lever — the next attempt must attack signal *strength* structurally, not add more features to the same thin construction.

This is not defeatism. The cross-sectional architecture is the only v3 line in three cycles with a *genuine, statistically-significant, OOS-positive signal transfer* — that is real and worth pursuing. But the line must be carried forward with an honest ledger: one architecture stand-up, one mechanical fix, one failed edge attempt. /091 is the iteration that decides whether the cross-sectional gross signal can be made strong enough to matter.

---

## 6. Critic recommendations — integration

The Critic's Phase-7.5 review closed with three process-level recommendations. All three are integrated:

1. **Make gross monthly Sharpe a reproducible runner artifact.** RECORDED as a **/091 mandatory SETUP item** (Section 7.4). The cross-sectional runner (`run_cross_sectional_v3.py` / `cross_sectional.py`) must emit `gross_monthly_sharpe` (IS + OOS) to `comparison.csv` and `dsr.json`, computed by the *identical* per-month code path as `monthly_sharpe`, with a smoke test asserting the two share the code path. This is QE work — flagged here, NOT done by the QR (the QR does not modify `src`/runner code). The root cause of this BLOCK is that gross monthly Sharpe was a hand-computation; per `feedback_v3_methodology_axis_integration_test.md`, any metric that drives a falsifier (F3) must be a runner output.
2. **Recompute /090's OOS gross monthly Sharpe and re-evaluate F3 before filing the classification.** DONE — Section 2 (recompute) and Section 3 (F3 re-evaluation + classification). The classification is filed on the corrected +0.1558-vs-+0.1717 comparison, not the report's +0.5398-vs-+0.5947.
3. **The /091 brief must anchor on the correct gross figures and re-state the trajectory honestly.** RECORDED — Section 5 above re-states the trajectory honestly (two mechanical gains + one failed edge attempt); the /091 brief must anchor on /089's correct OOS gross monthly Sharpe +0.1717 and /090's recomputed +0.1558, never the +0.5947/+0.5398 pair.

---

## 7. iter-v3/091 — Next Iteration Ideas (the forward plan)

iter-v3/091 is cycle-3 EXPLORATION slot #10 of 10. After /091, cycle 3's 10-EXPLORATION cadence is complete and iter-v3/092 is the cycle-3 CONFIRMATION.

### 7.1 — The constraint /090 imposes on /091

The /090 brief Section 3.6 *pre-registered* a "short-tilt / asymmetric-leg construction" as the /091 axis. **/091 must NOT default to it.** The Critic's point is correct and decisive: a short-tilt construction *re-slices the same thin gross signal* — it changes how the long-short book is cut, not how strong the underlying signal is. The /090 finding is that the gross signal itself is too thin (OOS gross monthly Sharpe +0.16). Re-slicing a +0.16 gross book into a short-tilted +0.16 gross book does not create edge; at best it captures a few bps of the long/short asymmetry the A-block measured (tercile asymmetry only 1.38×). With the gross signal failing to respond to feature work, the open question is **signal strength**, and a construction re-slice does not address it. The pre-registered short-tilt axis is *deferred* — it becomes relevant only once the gross signal is strong enough that the leg-asymmetry is worth harvesting.

The honest finding /091 must build on: **the cross-sectional gross signal in the current 22-altcoin / ~1-day-hold / momentum-rank construction is too thin to monetize at the current cost structure.** The bold response is to attack signal STRENGTH structurally.

### 7.2 — Three research-grounded candidate /091 axes

Cross-sectional momentum in equities (the AQR / Two Sigma playbook) earns its edge from four structural sources the current v3 cross-sectional construction is weak on: (i) *many more names* → wider cross-sectional dispersion → more reliable rank ordering; (ii) *multiple orthogonal factors* → diversified alpha; (iii) *longer holding horizons* → less turnover, signal measured where it actually persists; (iv) *careful risk neutralization*. /090 ruled out feature work within the current construction. The three candidates below each attack a different one of (i)-(iii). The full /091 brief with committed IS-EDA is /091's own Phase 1-5 — this is the researched starting point, per `feedback_v3_axis_selection_quant_discipline.md` the /091 QR commits the EDA before the brief.

**Candidate A — LONGER HOLDING HORIZON (RECOMMENDED).** The current cross-sectional hold is `XS_HOLD_BARS = 3` = 3 × 8h = **~1 day**. The cross-sectional crypto-momentum literature is consistent and specific: the signal persists at *weekly-to-fortnightly* horizons and *reverses* beyond ~2 weeks. Han, Kang & Ryu (SSRN 4675565) — *"returns are positive and statistically significant for sorting/holding horizons up to 2 weeks, become insignificant for 2-4 weeks, then negative."* The practitioner consensus (FXEmpire, starkiller.capital) — *"sort into quintiles on 2-week cumulative returns, hold one week, rebalance weekly"*; *"greatest monotonicity and return spread for lookback 10-35 days with 7-day rebalancing."* The current ~1-day hold is **below** the horizon where the cross-sectional signal lives — it is harvesting the noisiest, fastest-decaying, most cost-exposed slice. A move to a ~7-day hold (`XS_HOLD_BARS = 21`) attacks the problem on two axes at once: (a) it measures the signal at the horizon the literature says it is strongest and most stable — a genuine *signal-strength* lever, not a re-slice; (b) it cuts rebalance frequency ~7× → collapses the fee drag that is the *sole* source of the net loss (OOS fees/gross 1.58×). This is the highest-EV /091 axis: it is the one structural change that plausibly moves the OOS book net-positive, it is grounded in a clear, specific, multi-source literature, and it directly targets the diagnosed failure (a thin gross signal *and* a fee drag). The IS-EDA must scan the hold-horizon grid (e.g. {3, 7, 14, 21, 28, 35} bars) for the IS quintile long-short spread Sharpe *net of cost*, and pre-register the IS-best — and must check the label horizon: a longer hold may motivate re-deriving the H=3 forward-return-rank label to a horizon-matched H, which would change `XS_REQUIRED_GAP` (a SETUP consequence to flag).

**Candidate B — MULTI-FACTOR CROSS-SECTIONAL CONSTRUCTION.** The current ranker is a single-factor object — a momentum-rank model (the 13-15 features are overwhelmingly trailing-return / volatility transforms of one signal family). The cross-sectional equity playbook and the crypto practitioner literature both say single-factor is the wrong target: unravel.finance — *"beyond about six factors marginal benefit drops to near zero; it is easier to build three orthogonal portfolios with Sharpe ≈ 2.5 than to squeeze a single portfolio up to Sharpe 3."* Liu, Tsyvinski & Wu (*JoF* 2022) established that **size and momentum are *distinct* priced cross-sectional crypto factors**. /091-B would construct *separate* cross-sectional factor books — momentum-rank (the current model), a size/liquidity-rank book, a low-idiosyncratic-volatility-rank book (the /090 B1 family that tested *positive* incremental but was not the strongest single family) — and combine them as orthogonal sleeves rather than dumping all features into one ranker (which the /090 colsample-dilution finding shows the LGBMRanker handles poorly). This attacks signal strength via *diversification* of alpha sources. The risk: it is a larger re-architecture than A and harder to keep single-axis; and /090 already showed that *adding* signal families to the *same ranker* fails — /091-B only makes sense as *separate* books, which is a construction re-architecture. Recommended as the /092+ direction if /091-A transfers, not as /091 itself.

**Candidate C — crypto CARRY factor (funding-rate cross-sectional rank). NOT RECOMMENDED.** A "soft carry" cross-sectional book — long the lowest-funding-rate coins, short the highest — is a genuine crypto-native factor (BIS WP 1087; unravel.finance), orthogonal to momentum. But two findings rule it out for /091. (1) **Carry has decayed precisely in the v3 OOS window.** The 2024-25 crypto-carry research is explicit: the crypto carry-strategy Sharpe *fell to 4.06 in 2024 and turned negative in 2025* — and the v3 OOS window is 2025-03 → 2026-05. A carry factor would be tested on the exact window where carry stopped working. (2) **Funding data availability + the per-symbol runner's funding-feature ban.** iter-v3/019's funding-rate axis fired PROMISING-INERT on the per-symbol architecture (importance rank 14/14); the /088/089 diaries note the 7-feed structural verdict was established on the per-symbol architecture and is *not categorically* binding on a cross-sectional ranker — but the /090 finding (adding a weak feature family to the cross-sectional ranker *harms* it via colsample dilution) means a funding feature would have to clear a high bar, and the carry-decay finding says it would not. Carry is recorded as a researched-and-rejected candidate; do not retest it without new evidence that crypto carry has recovered post-2025.

### 7.3 — Recommendation: /091 axis = LONGER HOLDING HORIZON (Candidate A)

**The /091 EXPLORATION axis should be the holding-horizon extension** — move `XS_HOLD_BARS` from 3 (~1 day) toward ~7 days (~21 bars), IS-EDA-selected from a scanned hold-horizon grid. Rationale, ranked:

1. It is the single change that attacks **both** diagnosed failure modes — a thin gross signal (it measures the signal at the horizon the literature says it is strongest) and the fee drag (it cuts rebalance frequency ~7×, collapsing the OOS fees/gross 1.58×).
2. It is grounded in a **clear, specific, multi-source literature** (Han-Kang-Ryu SSRN 4675565; the FXEmpire / starkiller practitioner consensus; Dobrynskaya on crypto momentum-then-reversal) that all converge on weekly-to-fortnightly as the cross-sectional crypto-momentum horizon — the current ~1-day hold is demonstrably below it.
3. It is a **genuine signal-strength lever, not a re-slice** — it changes *which slice of the return process the signal is measured on*, directly answering the open question /090 raised.
4. It is a **single, clean, well-scoped axis** — a construction-horizon change, EDA-gridded and IS-pre-registered, testable in one EXPLORATION. It does not stack two axes.

Universe expansion (22 → 50+) was a candidate the Critic itself raised, and it does attack "the signal is too thin" via wider dispersion — but the literature is a *warning* here: unravel.finance — *"most returns come from top-40 market-cap coins; smaller tokens suffer liquidity constraints and higher idiosyncratic risk"*; the crypto cross-sectional literature — *"most crypto assets outside large-cap names behave like penny stocks: thinly traded, highly volatile, pump-and-dump."* Expanding to 50+ pushes the universe *into* the illiquid tail where cross-sectional signals are noisiest and least tradeable — and v3's per-symbol track already has a documented dead-path of universe expansions that drag (AAVE/AVAX/ATOM, and the cross-sectional /083 +FIL, /087 +GALA+MANA+SAND both NEGATIVE). Universe expansion is recorded as a *lower-priority* /091 candidate — it is a real lever but the liquidity-tail risk makes it second to the holding-horizon axis, which has no such downside. The /091 QR may revisit it if the holding-horizon EDA is inconclusive.

### 7.4 — /091 mandatory SETUP item (Critic Rec #1) — flagged for QE, not done here

**The cross-sectional runner must emit gross monthly Sharpe as a reproducible artifact.** `run_cross_sectional_v3.py` / `cross_sectional.py` must compute `gross_monthly_sharpe` (IS and OOS) by the *identical* per-calendar-month code path that produces `monthly_sharpe`, and write it to `comparison.csv` and `dsr.json`. A smoke test must assert `gross_monthly_sharpe` and `monthly_sharpe` are produced by the same aggregation function (e.g. both call one `_monthly_sharpe(pnl_column)` helper). This closes the root cause of the /090 BLOCK — a falsifier-driving metric (F3) computed by hand with no reproducible derivation, producing two different numbers (+0.1717, +0.5947) for the same /089 data. **This is QE work in `src`/runner code — the QR does not implement it; it is flagged here as a mandatory /091 setup-commit item per `feedback_v3_methodology_axis_integration_test.md`.** The /091 QR should reference this item in the brief Section 9 (integration-test mandate); the /091 Engineer implements it at the setup commit before the /091 axis change.

### 7.5 — Cycle-3 progress

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /082 | funding-rate 4-channel feature family | SUSPICIOUS-OOS-DOMINANT |
| #2 | /083 | universe expansion 3→4 (+FIL) | NEGATIVE |
| #3 | /084 | REFERENCE / methodology re-anchor | REFERENCE-REANCHOR |
| #4 | /085 | funding-regime-conditioned engineered feature | SUSPICIOUS |
| #5 | /086 | perp-spot basis 3-feature family | INERT |
| #6 | /087 | universe expansion 3→6 (+GALA+MANA+SAND) | NEGATIVE |
| #7 | /088 | RE-ARCHITECTURE — cross-sectional `LGBMRanker` | ARCHITECTURE-PARTIAL |
| #8 | /089 | corrected cross-sectional (sign fix + cost-aware construction) | CONSTRUCTION-PARTIAL |
| #9 | **/090** | **cross-sectional downside-risk feature expansion** | **FEATURE-EXPANSION-FALSIFIED / Critic OVERALL=BLOCK** |
| #10 | /091 | cross-sectional holding-horizon extension (recommended) | — |
| CONFIRMATION | /092 | best cycle-3 result (multi-seed validation) | pre-registered MERGE gates |

Cycle 3 has used 9 of 10 EXPLORATION slots — 0 clean PROMISING. /088/089 stood up and corrected the cross-sectional architecture; /090 established that feature expansion is not the lever to grow its thin gross signal. /091 (holding-horizon extension) is the final cycle-3 EXPLORATION and the iteration that tests whether the cross-sectional gross signal can be made strong enough — by measuring it at the horizon the literature says it lives — to carry the OOS book net-positive.

---

## 8. Decision

**NO-MERGE. Critic Phase-7.5 OVERALL = BLOCK (FINAL).** iter-v3/090 classified **FEATURE-EXPANSION-FALSIFIED** (brief Section 8.2) on the corrected gross-Sharpe recompute: F3 fires — /090 OOS gross monthly Sharpe +0.1558 ≤ /089's +0.1717. The 2 downside-risk features (`xs_sortino_mom_12`, `xs_downbeta_50`) are **DROPPED** — they did not strengthen the cross-sectional gross signal (OOS gross −0.0159; IS gross also fell; `frac_positive_paths` 0.356 → 0.200).

The BLOCK is a process-integrity finding: the engineering report's central diagnostic was a hand-computed gross-Sharpe metric on a non-per-month basis with a wrong (+0.5947) /089 anchor, driving falsifier F3. The number is corrected in this closeout (`analysis/iteration_v3-090/gross_sharpe_recompute.py` — net validations reproduce comparison.csv / monthly_pnl.csv to 1e-14; /089 OOS gross recomputes to +0.171676, vindicating the documented +0.1717). The /091 setup commit must make gross monthly Sharpe a reproducible runner artifact (Critic Rec #1; QE work, flagged Section 7.4).

**BASELINE_V3.md is UNCHANGED** — canonical /059 metrics (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791), tag `v0.v3-059`. An EXPLORATION never updates the baseline. `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` untouched.

The cross-sectional architecture, `cross_sectional.py` infrastructure, the 22-symbol `XS_UNIVERSE`, and the /089 cost-aware construction are **RETAINED** as the active v3 research line — 8.2 falsifies only the /090 feature additions, not the architecture. **The honest trajectory: /088 architecture stand-up → /089 +0.44 MECHANICAL gain (sign fix + turnover cut) → /090 first genuine gross-edge attempt, FAILED.** Two mechanical gains plus one failed edge attempt — not an unbroken ascent. /091's EXPLORATION axis is the **holding-horizon extension** (`XS_HOLD_BARS` 3 → ~21, IS-EDA-gridded) — the highest-EV remaining lever: it measures the cross-sectional momentum signal at the weekly-to-fortnightly horizon the literature says it lives, and cuts the fee drag ~7×. An EXPLORATION closeout marker tag `v0.v3-090` is issued (annotated; NOT a baseline update — the `v0.v3-082`…`v0.v3-089` pattern).

---

**Commit chain:**
- EDA SHA: `cecbc8f` — `analysis/iteration_v3-090/gross_signal_expansion_eda.py` + `b2_feature_selection_eda.py`
- Brief SHA: `bb425a5` — `briefs-v3/iteration_v3-090/research_brief.md`; Phase 5.5 gate `55979e7` (PASS — independent QE gate, supersedes the QR self-gate `662d7cc`)
- Setup SHA: `a584fdf` — `XS_DOWNSIDE_FEATURES` + `_engineer_xs_downside_features` + `expand_downside` panel branch; `XS_FEATURE_COLUMNS` → 15; `ITERATION_LABEL "v3-090"`
- Engineering report SHA: `26e3bed` — `briefs-v3/iteration_v3-090/engineering_report.md`
- Critic FINAL SHA: `95065ee` — `briefs-v3/iteration_v3-090/review.md` — **OVERALL=BLOCK** (methodology DEFECT in the engineering report's central gross-Sharpe diagnostic)
- Closeout recompute SHA: `b07cbe9` — `analysis/iteration_v3-090/gross_sharpe_recompute.py` + `gross_sharpe_recompute_output.txt` (Critic Rec #2)
- Diary + catalog SHA: `acede0c` — `docs(iter-v3/090): closeout diary + catalog — FEATURE-EXPANSION-FALSIFIED / Critic OVERALL=BLOCK`
**Reports**: `reports-v3/iteration_v3-090/`
**Tag**: `v0.v3-090` (EXPLORATION closeout marker; NOT a baseline update — BASELINE_V3.md UNCHANGED at `v0.v3-059`)
