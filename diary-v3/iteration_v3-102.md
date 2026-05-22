# Iteration iter-v3/102 — Diary

## Decision: EXPLORATION-NEGATIVE — Falsifier F2 fires (IS monthly Sharpe collapse to +0.3993, below the +0.60 floor). NO-MERGE; non-advancing.

iter-v3/102 (cycle-5 EXPLORATION slot #2) tested **ONE variable**: the WorldQuant
formulaic alpha **`alpha032`** added to `V3_FEATURE_COLUMNS`, taking the v3 per-symbol
feature stack from 14 to 15 columns. `alpha032` is a v3-portable per-symbol port of
Kakushadze (2015, arXiv 1601.00991) Alpha#32 —
`scale_ts((sum(close,7)/7 − close), 100) + 20·scale_ts(corr(vwap, delay(close,5), 230), 100)`
— a fast SMA-gap mean-reversion term plus a slow vwap/lagged-close lead-lag correlation
term. No label change, no model-arch change, no universe change, no risk-gate change.

Phase-7.5 Critic OVERALL=MERGE — no methodology BLOCK. **Critically, Check 1 (Look-Ahead)
is PASS**: the Critic traced `compute_alpha032` line-by-line and confirmed it is strictly
past-only (every rolling window has `min_periods == window`, no centered window, no
full-series operation, no `bfill`; the QE's `test_hard_causality` regression test is
genuine — `max_abs_diff = 0.0` when 50 future bars are removed). The OOS +1.5458 spike is
therefore **NOT a look-ahead leak**.

On the QR Phase-8 read, the verdict is **EXPLORATION-NEGATIVE**: the pre-registered
Falsifier F2 fires — IS monthly Sharpe collapsed to **+0.3993**, far below the +0.60
floor. `alpha032` **REVERTS** (NEGATIVE, not carried forward); WorldQuant Alpha#32 is
recorded as a dead idea.

---

## Section 1 — What Was Done

### The axis (one variable, per the Critic-verified single-axis claim)

A new track-isolated module `src/crypto_trade/features_v3/formulaic_v3.py` provides
`compute_alpha032` and an `add_formulaic_v3_features` GROUP_REGISTRY entry point.
`alpha032` was appended as the 15th element of `V3_FEATURE_COLUMNS_TOP_N` (after
`regime_momentum_signed_5d`); `_verify_feature_columns` expected count bumped 14→15 with
an explicit `"alpha032" in V3_FEATURE_COLUMNS` positive assertion; `ITERATION_LABEL`
bumped to `"v3-102"`. The BCH/LDO/TRX v3 feature parquets were regenerated so `alpha032`
is present (BCH 6656/6989, LDO 3670/4003, TRX 6598/6931 valid rows — ~92–95%, the
~333-bar warm-up dominated by the 230-bar correlation window). The 14 incumbent
`V3_FEATURE_COLUMNS`, the BCH/LDO/TRX universe, ATR multipliers (2.0/1.0), the 21-candle
timeout, and the 7-gate RiskV2 stack are all bit-identical to /059.

### Backtest

3-seed EXPLORATION mode (`--exploration`, `EXPLORATION_ENSEMBLE_SIZE=3`, `--n-trials 35`).
Engineering report committed (Phase 6 setup commit `556c345`, Phase 5.5 gate `bc2a30a`);
Phase-7.5 Critic OVERALL=MERGE. Headline: IS monthly Sharpe **+0.3993** / OOS monthly
Sharpe **+1.5458**; 270 trades (177 IS, 93 OOS).

---

## Section 2 — The Anchor (matched, per cycle-5 discipline)

Per `feedback_v3_dsr_mode_artifact.md` and `feedback_v3_cycle1_axis_pass_criteria.md`,
and per the /101 closeout Lesson 3 (anchor-architecture-matching is verdict-determining),
a 3-seed EXPLORATION-mode run is classified against the **3-seed EXPLORATION-mode
reference /060** (IS monthly Sharpe **+0.8325** / OOS monthly Sharpe **+0.1403**), NOT the
10-seed /059 CONFIRMATION baseline (IS +1.0894 / OOS +0.5791). The /102 brief Section 4
applied this matching from the start — no anchor correction was needed in Phase 8 (unlike
/101).

| Metric | /102 (3-seed EXPL) | /060 anchor (3-seed EXPL) | Δ vs /060 |
|---|---:|---:|---:|
| **IS monthly Sharpe** | **+0.3993** | **+0.8325** | **−0.4332** |
| **OOS monthly Sharpe** | **+1.5458** | **+0.1403** | **+1.4055** |
| IS daily Sharpe | 1.0351 | — | — |
| OOS daily Sharpe | 3.9292 | — | — |
| OOS/IS monthly ratio | 3.8714 | 0.1685 | — |
| IS trades | 177 | 159 | +18 |
| OOS trades | 93 | 102 | −9 |
| frac_positive_paths | 0.6444 | 0.6444 | 0.000 (CPCV-invariant) |
| PBO | 0.1276 | 0.1278 | −0.0002 |
| n_eff | 19 | — | — |

Against the matched /060 anchor, /102 is **IS Δ −0.43 / OOS Δ +1.41** — an IS-collapse /
OOS-spike divergence. This is the **iter-v3/026/027/030/034/036/037 single-seed
overfitting signature** (and the same shape /082/085 funding-axis runs exhibited): the
added feature breaks the in-sample fit while the OOS headline spikes for reasons that are
not signal.

DSR=0.0 / PSR=1.0 / DSR_relative_b4=1.0 / n_eff=19 are EXPLORATION-mode artifacts
(`n_trials=315` vs CONFIRMATION's 1050) — INFORMATIONAL ONLY per
`feedback_v3_dsr_mode_artifact.md`, not classification inputs. The brief's PROMISING gate
in any case requires IS ≥ +0.60, which is not met.

---

## Section 3 — Per-Symbol Decomposition

**IS** (`in_sample/per_symbol.csv`):

| Symbol | IS trades | IS WR | IS net_pnl_pct | IS share |
|---|---:|---:|---:|---:|
| BCH | 82 | 45.1% | **+70.05** | 233.25% (denominator-inflated) |
| LDO | 8 | 25.0% | −17.22 | −57.35% |
| TRX | 87 | 32.2% | **−22.79** | −75.90% |

**OOS** (`out_of_sample/per_symbol.csv`):

| Symbol | OOS trades | OOS WR | OOS net_pnl_pct | OOS share |
|---|---:|---:|---:|---:|
| BCH | 29 | 55.2% | +55.30 | 69.42% |
| TRX | 52 | 51.9% | +34.98 | 43.92% |
| LDO | 12 | 33.3% | −10.62 | −13.34% |

The IS collapse is structural. The /059-canonical baseline carries BCH at ~95.76% of IS
PnL — BCH is the IS engine. With `alpha032` added, **BCH IS net_pnl_pct is only +70.05
at a 45.1% win rate, and TRX IS is −22.79 (a drag)**. The IS aggregate monthly Sharpe is
+0.3993 — `comparison.csv` IS profit_factor is only 1.1558 and IS win rate 32.20%. The
feature did not strengthen the IS fit; it degraded it. (The brief's T8 EDA had predicted
`alpha032` would *help* the IS-dominant symbol — BCH held-out d_acc +0.0591. The
multi-seed Optuna IS fit shows the opposite: see Section 5.)

The OOS side is the inverse — BCH +55.30 and TRX +34.98 are both positive, OOS win rate
49.46%, OOS profit_factor 1.6791. But this OOS strength sits on top of a collapsed IS
fit, which is precisely the overfitting signature, not an edge (Section 6).

---

## Section 4 — F1–F5 Falsifier Cross-Audit

Every brief Section-4 pre-registered falsifier, re-evaluated against the committed
artifacts. Anchor = /060 (3-seed EXPLORATION-mode).

| # | Falsifier | Threshold | Observed | Fires? |
|---|---|---|---|---|
| F1 | Headline OOS regression | OOS monthly Sharpe < +0.00 | **+1.5458** | **NO** |
| F2 | IS collapse | IS monthly Sharpe < +0.60 | **+0.3993** | **FIRES** |
| F3 | BCH-only artifact | OOS lift carried entirely by BCH AND **both** LDO and TRX OOS wpnl regress vs /060 | BCH +55.30 / **TRX +34.98 (positive — does NOT regress)** / LDO −10.62. The "both LDO and TRX regress" leg is FALSE — TRX OOS is materially positive. | **NO** |
| F4 | INERT by importance | `alpha032` gain-importance rank last (15/15) in **all 3** models OR combined share < 1/15 = 0.0667 in **all 3** | Last-IS-month rank: **BCH 8/15**, TRX 11/15, LDO 15/15 — last in only 1 of 3, NOT all 3. Share: portfolio 333.33/≈6953 ≈ 4.79% (sub-parity) but **BCH 132.33/≈1936 ≈ 6.84% — above the 1/15 parity** — so not sub-parity in all 3 either. `alpha032` is **LEARNED** (BCH rank 8/15, mid-table). | **NO** |
| F5 | Mechanical roster-churn | OOS improves AND per-symbol added-vs-removed mean-duration gap > +1.0 on any symbol with a material OOS lift | Not the binding falsifier — **F2 fires at step 2 (NEGATIVE), which precedes SUSPICIOUS (step 3) in the LOCKED disjunctive taxonomy; first match wins.** A roster-diff would be required to evaluate F5 (per the /101 Critic Rec 3), but the classification is settled at F2 before step 3 is reached. F5 is recorded as NOT EVALUATED — moot under precedence. | **N/A (moot)** |

**F2 FIRES.** F1, F3, F4 do NOT fire. F5 is moot under disjunctive precedence (F2 at
step 2 precedes SUSPICIOUS at step 3).

Note on F4 specifically: `alpha032` is NOT an INERT feature in the /019/082/085/086
sense — the tree genuinely allocated split capacity to it (BCH rank 8/15, portfolio rank
14/15 but with a non-trivial 4.79% share, not the rank-15/15 INERT pattern). This is an
important distinction: a LEARNED feature that still collapses IS is worse than an INERT
one — an INERT feature is merely ignored, whereas `alpha032` was learned and the IS fit
got worse, which is the over-allocation-of-noise mechanism `feedback_v3_inert_features_at_higher_budget.md`
describes (Optuna at n_trials=35 overfits IS noise *through* the 15th feature).

**SUSPICIOUS sub-check (brief Section 8 step 3, second leg) — recorded for completeness
even though step 2 already binds.** The structurally-suspicious IS/OOS divergence test is
keyed to the **daily** Sharpe ratio. From `comparison.csv`: IS daily Sharpe 1.0351, OOS
daily Sharpe 3.9292 → ratio **3.7960**, inside the [0.2, 5] sane band. So the
ratio-leg of SUSPICIOUS does **NOT** fire. /102 does not even reach step 3 — F2 places it
at step 2 (NEGATIVE) — but had it, the ratio leg would not have triggered. The
monthly-Sharpe ratio (3.8714) is similarly inside [0.2, 5]. **The divergence is real and
severe in absolute terms (IS −0.43 / OOS +1.41), but it does not trip the SUSPICIOUS
ratio gate; it trips F2 directly.** The classification is F2 → NEGATIVE.

---

## Section 5 — The IS-Collapse, and Why It Is NOT Look-Ahead (Critic Recommendation 1)

The Phase-7.5 Critic Recommendation 1 directs the QR to document the IS-collapse
explicitly and separate it from look-ahead. This section does that.

**The IS-collapse is a fitting failure, not a leak.** The Critic's Check 1 traced
`compute_alpha032` and confirmed strict past-only computation — every rolling window has
`min_periods == window` (no partial window straddles a train/test boundary), no centered
window, no full-series operation, no `bfill`; `delay(close,5)` is `.shift(5)`. The QE's
`test_hard_causality` regression test (`max_abs_diff = 0.0` when 50 future bars are
removed) is genuine and sufficient, and the EDA's T3 adversarial audit found 0/54
(alpha × symbol) cells fail. **There is no information path from the OOS window into the
feature.** The OOS +1.5458 is therefore not a look-ahead spike — it is overfitting plus
OOS-regime luck.

**The IS-collapse mechanism.** Adding `alpha032` as the 15th feature widened the
per-symbol Optuna search space. The tree LEARNED `alpha032` (BCH rank 8/15 — it was
allocated genuine split capacity), but at `n_trials=35` the larger space let Optuna
overfit the IS noise — *including* the noise component of `alpha032` — and the IS fit
degraded. IS monthly Sharpe fell to +0.3993 (Δ −0.43 vs /060), IS profit_factor only
1.1558, IS win rate 32.20%, BCH IS net_pnl_pct down to +70.05 at a 45.1% win rate. This
is the *exact* mechanism `feedback_v3_inert_features_at_higher_budget.md` documents (and
a degree worse — here the feature is learned, not inert).

**Why the OOS headline still spiked.** With the IS fit broken, the fitted models'
behavior in the OOS window is no longer a controlled extrapolation of a healthy IS fit —
it is a roll of the dice over a directional OOS window. /102's OOS window happens to
contain enough directional moves (BCH OOS +55.30, TRX OOS +34.98) that the
noise-overfit models score well. The OOS daily Sharpe 3.9292 on only 79 daily
observations across 93 OOS trades is itself a thin-sample, high-variance number. **An OOS
spike sitting on a collapsed IS fit is the textbook overfitting signature** — it is the
iter-v3/026/027/030/034/036/037 pattern, and it is why the v3 taxonomy puts the F2
IS-collapse gate at step 2, ahead of any OOS-based classification. The OOS +1.5458 is
**not an edge**.

---

## Section 6 — Brief Section-7 Pre-Registered Failure-Mode Prediction vs Actual

The brief Section 7 pre-registered three failure modes in probability order:

1. **Most-likely: INERT (Falsifier F4)** — "the per-symbol depth-3-5 LightGBM allocates
   little split gain to it and the OOS roster barely moves … `alpha032` recorded as INERT
   … formulaic-alpha axis closed at one data point."
2. **Second: SUSPICIOUS via F5 (roster-churn)** — the /101-Lesson-2 trade-selection
   sub-channel.
3. **Third: NEGATIVE (F1/F2/F3)** — "`alpha032` could break the IS fit (F2 — the /063
   mass-expansion mode) or be a pure BCH artifact (F3)."

**The prediction was partially right and the specific ranking missed:**

- **The actual outcome is NEGATIVE via F2** — the brief's *third*-ranked mode, and
  specifically the F2 sub-mode the brief explicitly named ("could break the IS fit
  (F2 — the /063 mass-expansion mode)"). So the *direction* was anticipated: the brief
  did pre-register F2, did name "break the IS fit" as a live risk, and did cite the /063
  mass-expansion precedent as the IS-collapse analogue.
- **But the probability ranking missed.** The brief called INERT most-likely and NEGATIVE
  only third. The actual is NEGATIVE, and not even via INERT-adjacent reasoning: F4
  explicitly did NOT fire — `alpha032` was LEARNED (BCH rank 8/15, a non-trivial 4.79%
  portfolio share), not ignored. The modal predicted outcome (INERT) is therefore the one
  outcome that is most clearly *wrong* about the mechanism: the tree did allocate split
  capacity, and that is part of *why* IS collapsed. The brief's reasoning that
  `alpha032`'s thin univariate IC and middling sign-stability would lead to INERT
  under-allocation got the allocation backwards — the feature was used, and using it hurt.
- **F3 (the BCH-only-artifact mode) also did not fire** — TRX OOS is materially positive
  (+34.98), so the F3 "both LDO and TRX regress" leg is false.

**Honest accounting — this matches the /101 pattern.** As with /101, the failure
*direction* was partly anticipated (the brief pre-registered F2 and named IS-collapse as
a genuine risk, citing /063) but the specific falsifier *ranking* missed (the brief ranked
INERT #1 / NEGATIVE #3; the actual is NEGATIVE-via-F2, and INERT is mechanistically
contradicted by the rank-8/15 BCH allocation). The brief's Section-7 reasoning treated a
thin-univariate-IC feature as one the tree would *ignore*; the truer v3 risk — repeatedly
documented — is that the tree *uses* a marginal feature and the larger search space then
overfits IS. The next formulaic-alpha-class brief, if any, should rank
NEGATIVE-via-IS-collapse as a *leading* mode for any single-feature addition, not a
third-place mode.

---

## Section 7 — Classification: EXPLORATION-NEGATIVE

**Anchor used:** /060 (3-seed EXPLORATION-mode, IS +0.8325 / OOS +0.1403) — the
architecturally-matched reference, per `feedback_v3_dsr_mode_artifact.md` +
`feedback_v3_cycle1_axis_pass_criteria.md`.

**Classification:** **EXPLORATION-NEGATIVE** — brief Section 8 LOCKED disjunctive
taxonomy **step 2** (Falsifier F2 fires: IS monthly Sharpe +0.3993 < +0.60). First match
wins. **NO-MERGE; non-advancing.**

**Why NEGATIVE and not the neighbors — explicit reasoning:**

- **Not BLOCKED (step 1):** the Phase-7.5 Critic returned OVERALL=MERGE — no methodology
  defect, **look-ahead clean** (Check 1 PASS — `compute_alpha032` traced strictly
  past-only), DSR/PBO/PSR genuinely computed (not the /090/092 placeholder defect). Step
  1 does not apply.

- **NEGATIVE (step 2) — the match.** Falsifier F2 fires: IS monthly Sharpe is **+0.3993**,
  below the pre-registered +0.60 floor by 0.20 (Δ −0.43 vs the /060 anchor +0.8325).
  `alpha032` broke the in-sample fit — the /063 mass-expansion failure mode the brief
  itself named. F2 is the first matching step in the disjunctive precedence and therefore
  the verdict. (F1 does not fire — OOS +1.5458; F3 does not fire — TRX OOS positive.)

- **Not SUSPICIOUS (step 3) — unreachable, and would not fire on the merits either.**
  Step 3 is unreachable because step 2 (F2) already matched. On the merits: the
  SUSPICIOUS ratio-leg is keyed to the **daily** Sharpe ratio — observed 3.7960
  (`comparison.csv` daily 1.0351 IS / 3.9292 OOS), inside [0.2, 5] — so the ratio leg
  would NOT have fired; and F5 was not evaluated (moot under precedence). SUSPICIOUS is
  rejected on both precedence and the ratio leg. **Note for the record:** the IS −0.43 /
  OOS +1.41 divergence IS the overfitting signature in *substance* — but the v3 taxonomy
  routes a *measured IS collapse below the F2 floor* to NEGATIVE (step 2), reserving
  SUSPICIOUS (step 3) for cases where IS holds above the floor but the IS/OOS *ratio* is
  pathological. /102's IS does not hold — it collapses outright — so it is NEGATIVE, not
  SUSPICIOUS.

- **Not INERT (step 4) — unreachable, and contradicted on the merits.** Step 4 is
  unreachable (step 2 matched). On the merits: F4 explicitly does NOT fire — `alpha032`
  is LEARNED, not ignored (BCH last-IS-month rank 8/15, mid-table; portfolio rank 14/15
  but with a 4.79% share, not the rank-15/15 INERT pattern). The feature was behaviorally
  active. INERT is rejected on both precedence and substance.

- **Not PROMISING (step 5) — comprehensively blocked.** Three independent blocks:
  (1) the disjunctive precedence — F2 (step 2) fires, so step 5 is never reached, and
  PROMISING requires *none* of F1–F5 to fire; (2) the PROMISING gate explicitly requires
  IS monthly Sharpe ≥ +0.60 — observed +0.3993 fails it outright; (3) on the merits, the
  OOS +1.5458 is NOT a generalizable edge — it is an OOS spike sitting on a collapsed IS
  fit (Section 5), the iter-v3/026/027/030/034/036/037 overfitting signature, ruled
  NOT-a-leak by the Critic but equally NOT-an-edge by the QR. A PROMISING classification
  here would be the precise post-hoc rationalization the /101-Lesson and the dispatch
  instruction forbid. PROMISING is rejected.

- **Not NULL-RESULT (step 6) — unreachable, and not the right shape.** Step 6 is
  unreachable (step 2 matched). NULL-RESULT is the "fits none of the above cleanly"
  catch-all — /102 fits NEGATIVE cleanly via F2 (a pre-registered, numerically-precise
  falsifier firing). NULL-RESULT is rejected.

The honest one-line read: **/102 collapsed the in-sample fit (IS +0.3993, F2 fires) while
the OOS headline spiked to +1.5458 — and the Critic ruled the spike is NOT a look-ahead
leak, so it is the IS-collapse / OOS-spike overfitting signature; /102 is NEGATIVE,
neither a leak nor an edge.**

---

## Section 8 — Does `alpha032` carry forward? — NO. It REVERTS.

**`alpha032` is REVERTED. It does NOT carry to a cycle-5 CONFIRMATION and is NOT retained
in `V3_FEATURE_COLUMNS`.**

A NEGATIVE EXPLORATION never advances. The reasons, specific to /102:

1. **It broke the IS fit.** F2 fires — IS monthly Sharpe +0.3993, a 0.43 collapse vs the
   /060 anchor. `feedback_v3_strict_both_is_oos_baseline.md` requires a CONFIRMATION to
   improve BOTH IS and OOS over the /059 baseline; `alpha032` regresses IS hard. There is
   no IS-improvement thesis to carry.
2. **The OOS lift is not signal.** Section 5 establishes the OOS +1.5458 is an OOS spike
   on a collapsed IS fit — the iter-v3/026/027/030/034/036/037 overfitting signature. A
   10-seed CONFIRMATION would not validate an edge; it would re-measure a noise-overfit
   model's luck on a directional OOS window. The multi-seed ensemble averaging in a
   CONFIRMATION would, if anything, wash out the lottery component — but there is nothing
   underneath it to keep.
3. **`feedback_v3_inert_features_at_higher_budget.md` is binding.** That rule states a
   feature that harms OOS at higher budget must NOT be carried forward and must NOT be
   retested at a higher Optuna budget. `alpha032` is a *learned* feature that nonetheless
   collapsed IS — a sharper instance of the same harm. It must not be retested at the
   CONFIRMATION's n_trials=1050.

`run_baseline_v3.py` `V3_FEATURE_COLUMNS_TOP_N` reverts to the 14-feature /059 stack
(`alpha032` removed); `_verify_feature_columns` expected count reverts 15→14; the
`add_formulaic_v3_features` GROUP_REGISTRY entry is removed from the active feature build.
The `formulaic_v3.py` module + its unit tests stay in the tree at zero revert cost
(reusable infrastructure, the `fetch-spot`/`basis_v3.py` precedent from /086) — only the
feature column is dropped, and `"alpha032"` joins the runner ABSENT-assertion ban (the
`funding_regime_momentum_5d` / basis-feature pattern), so a future iteration cannot
silently re-add it.

**WorldQuant Alpha#32 is recorded as a dead idea** in BASELINE_V3.md Dead Ideas (per
Critic Recommendation 2 and the established v3 documentation convention) with the specific
failure mode — see Section 9. Recording a dead idea is documentation; it is NOT a
baseline-metric change.

---

## Section 9 — WorldQuant Alpha#32 as a Dead Idea (Critic Recommendation 2)

Per Critic Recommendation 2, **WorldQuant Alpha#32 (`alpha032`)** is recorded as a v3
dead idea. The specific, generalizable failure mode:

> **WorldQuant Alpha#32 (`alpha032`) — EXPLORATION-NEGATIVE at iter-v3/102.** A
> v3-portable per-symbol port of Kakushadze (2015, arXiv 1601.00991) Alpha#32 —
> `scale_ts((sum(close,7)/7 − close), 100) + 20·scale_ts(corr(vwap, delay(close,5), 230), 100)`,
> a fast SMA-gap mean-reversion term plus a slow vwap/lagged-close lead-lag correlation
> term — added as the 15th `V3_FEATURE_COLUMNS` feature. It was the **basket horse-race
> winner**: the /102 EDA screened 18 v3-portable time-series-pure WorldQuant-101 alphas
> and `alpha032` ranked **1/18** on the multivariate held-out-tail accuracy lift (EDA T6
> `dShACC` +0.01373) and 1/18 on the composite selection score (T7 1.897). **But its
> held-out-tail proxy CI straddled zero** — the T6 95% CI was [−0.0085, +0.0399], and the
> brief honestly recorded that no alpha in the basket cleared a CI lower bound > 0. At the
> 3-seed multi-seed Optuna backtest the feature **collapsed the in-sample fit**: IS
> monthly Sharpe fell to +0.3993 (Δ −0.43 vs the /060 EXPLORATION-mode anchor; F2 fires,
> < +0.60 floor), even though the tree genuinely *learned* `alpha032` (BCH last-IS-month
> importance rank 8/15, not INERT). The OOS headline spiked to +1.5458 — but the Phase-7.5
> Critic Check 1 traced `compute_alpha032` line-by-line and confirmed it is strictly
> past-only (`min_periods == window` on every rolling op, no centered/full-series
> operation, `test_hard_causality` max_abs_diff = 0.0), so the OOS spike is **NOT a
> look-ahead leak** — it is the iter-v3/026/027/030/034/036/037 IS-collapse / OOS-spike
> overfitting signature. **The generalizable lesson: a held-out-tail single-classifier
> accuracy proxy does NOT predict the multi-seed Optuna IS fit.** A basket horse-race that
> selects on held-out single-classifier accuracy (the /098 methodology) ranked `alpha032`
> 1/18 and predicted a BCH IS *gain* (T8 d_acc +0.0591); the actual multi-seed Optuna
> backtest, with a 15th feature widening the search space, *collapsed* BCH IS. A proxy
> whose own CI straddles zero is, at best, a relative ranking among candidates — it is not
> evidence of a multi-seed-survivable edge, and a positive point estimate on a
> CI-straddling-zero proxy is not a GO signal. `alpha032` must be **REVERTED** (NEGATIVE,
> not carried forward); it joins the runner ABSENT-assertion ban and must not be retested
> at a higher Optuna budget per `feedback_v3_inert_features_at_higher_budget.md`. The
> `formulaic_v3.py` module + unit tests are retained as reusable infrastructure; only the
> feature column is dropped. Detail: `diary-v3/iteration_v3-102.md`.

---

## Section 10 — BASELINE_V3.md Status: UNCHANGED

Per brief Section 8 and `feedback_v3_baseline_update_policy.md`: an EXPLORATION never
updates `BASELINE_V3.md` baseline metrics regardless of classification. /102 is
EXPLORATION-NEGATIVE — NO-MERGE. **BASELINE_V3.md baseline metrics are UNCHANGED**;
iter-v3/059 remains the canonical baseline (IS +1.0894 / OOS +0.5791, 10-seed
CONFIRMATION). Tag `v0.v3-102` is a **closeout marker only** (the `v0.v3-082`…`v0.v3-101`
pattern), not a baseline update.

The **only** BASELINE_V3.md edit is a new Dead Ideas entry recording WorldQuant Alpha#32
(Section 9) — documentation, not a baseline-metric change, and the established v3
convention (the /082/085/086/087 funding/basis/universe Dead Ideas entries).

`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` were not touched. The
walk-forward embargo fix (`e149e9d`) is inherited unchanged. No cheating: the QR saw OOS
for the first time in Phase 7; all Phase 1–5 EDA was IS-only (Phase-5.5 gate verified the
`open_time < OOS_CUTOFF_MS` mask in all 4 EDA scripts); the Phase-7 cross-audit reads
only committed report CSVs.

---

## Section 11 — Lessons

1. **A held-out-tail single-classifier accuracy proxy does not predict the multi-seed
   Optuna IS fit.** The /102 EDA's horse race (the /098 methodology) selected `alpha032`
   as the 1/18 basket winner on held-out-tail directional-accuracy lift and predicted a
   BCH IS *gain*. The 3-seed multi-seed Optuna backtest *collapsed* BCH IS. The proxy and
   the production fit are different objects: the proxy is a single classifier's held-out
   accuracy; the production number is a multi-seed Optuna ensemble's walk-forward Sharpe,
   and adding a 15th feature widens the Optuna search space in a way the proxy cannot see.
   When the proxy's own CI straddles zero (T6 [−0.0085, +0.0399]), the horse-race rank is
   a *relative ordering among candidates only* — not evidence of a survivable edge. A
   future formulaic-alpha or composed-feature EDA should treat a CI-straddling-zero
   horse-race winner as an inconclusive-and-likely-negative axis, not a GO.

2. **A LEARNED feature that collapses IS is worse than an INERT one.** The v3 INERT
   pattern (/019/082/085/086 — rank 15/15, the tree ignores the feature) is a *null*
   result: the model declines to use the feature, and the headline barely moves. /102 is
   different and worse — `alpha032` was *learned* (BCH rank 8/15, 4.79% portfolio share),
   and using it *degraded* the IS fit. This is the over-allocation-of-noise mechanism: at
   n_trials=35 a wider feature space lets Optuna fit IS noise *through* the new feature.
   F4 (INERT) and F2 (IS-collapse) are genuinely distinct outcomes — and a single-feature
   brief should rank NEGATIVE-via-IS-collapse as a *leading* predicted mode, not (as the
   /102 brief did) a third-place mode behind INERT.

3. **The IS-collapse / OOS-spike divergence is a recurring v3 single-seed failure mode,
   and the F2 gate (not the SUSPICIOUS ratio gate) is the one that catches it.** /102
   joins iter-v3/026/027/030/034/036/037 (and /082/085) in the IS-collapse / OOS-spike
   pattern. Two precision points the /102 closeout sharpens: (a) the Critic-verified
   look-ahead-clean finding means the OOS spike is *overfitting*, not a leak — the two
   must be separated explicitly (Critic Rec 1); (b) the SUSPICIOUS ratio gate is keyed to
   the *daily* Sharpe ratio (/102 observed 3.796, inside [0.2, 5]) and does NOT fire — the
   IS-collapse is caught by F2 directly (a measured IS Sharpe below the +0.60 floor),
   which sits at step 2 ahead of SUSPICIOUS at step 3. The taxonomy routes a *measured*
   IS collapse to NEGATIVE; SUSPICIOUS is reserved for an IS that holds above floor with a
   pathological ratio.

4. **The WorldQuant-101 formulaic-alpha axis closes at one data point — but more
   structurally, single-feature additions to the v3 14-feature stack keep failing.** The
   /102 brief's Section 7 noted v3's 7-FEED STRUCTURAL VERDICT (7 non-OHLCV crypto-native
   feature families, all INERT). `alpha032` is OHLCV-derived, so it is not an 8th feed —
   but it still failed, this time by IS-collapse rather than INERT. Across cycle 4 + cycle
   5, *every* feature-addition axis has failed: /098 (off-the-shelf families, NO-GO at
   EDA), the 7-FEED verdict, and now /102 (a formulaic alpha, NEGATIVE by IS-collapse).
   The binding constraint remains the thin per-symbol 8h triple-barrier signal; adding a
   15th feature to the existing per-symbol architecture does not lift it and tends to hurt
   the IS fit. Future EXPLORATIONs should weight a *new edge source / new architecture*
   over *another feature on the existing stack* (`feedback_v3_structural_over_knob_exploration.md`).

---

## Section 12 — Next Iteration Ideas (cycle-5 EXPLORATION slot #3 onward)

Feature-addition is now an attacked-and-repeatedly-closed v3 frame (the 7-FEED INERT
verdict; /098 NO-GO; /102 NEGATIVE-by-IS-collapse). Per
`feedback_v3_structural_over_knob_exploration.md` and the /101 closeout's Section-11
ranking, candidate axes for the next EXPLORATION, ranked:

1. **A genuinely new edge *source* requiring a data fetch + GO/NO-GO EDA.** Funding rates,
   OI, and perp-spot basis are closed for v3 (/019/023/024/082/085/086). Liquidation-
   cascade features and on-chain BTC-regime broadcasts (`references/crypto-edge-deep.md`)
   remain unattacked at the per-symbol-book layer. These require a fail-fast Phase-1
   GO/NO-GO EDA first (`feedback_fail_fast.md`) — the cheap kill that /094/095/096/098/099
   demonstrated.

2. **A regime-switching MODEL** (the /099→/100 lineage recommendation) — a per-symbol
   two-expert mixture: separate LightGBM models trained on trending vs mean-reverting
   sub-samples split by a past-only Hurst/ADX gate. Distinct from /093's regime
   size-overlay. Caveat: model-architecture changes have a poor v3 record (/016 XGBoost
   was the worst OOS Δ in v3 at −2.53).

3. **Universe expansion as denominator expansion** — HIGH-priority per
   `feedback_v3_iter019_axis_priorities.md` #2, but note Direction 2 is CLOSED for cycle 3
   at a 4-failure record (/021/069/083/087); a cycle-5 retry would need a materially
   different symbol-selection methodology and is lower-priority than (1) and (2).

Per `feedback_v3_axis_selection_quant_discipline.md`, the next axis must be QR-led with a
committed `analysis/iteration_v3-NNN/*.py` EDA basis before the brief. Per
`feedback_v3_strict_10_to_1_cadence.md`, cycle 5 runs 10 EXPLORATIONs before a
CONFIRMATION; /102 is slot #2.

---

## Reproducibility

- Iteration: iter-v3/102 — cycle-5 EXPLORATION slot #2
- Branch: `iteration-v3/102`
- Axis: add WorldQuant Alpha#32 (`alpha032`) to `V3_FEATURE_COLUMNS` (14 → 15) — one variable
- Run mode: 3-seed EXPLORATION (`--exploration`, `EXPLORATION_ENSEMBLE_SIZE=3`,
  `--n-trials 35`)
- Anchor for classification: iter-v3/060 (3-seed EXPLORATION-mode; IS +0.8325 / OOS +0.1403)
- Canonical baseline (unchanged): iter-v3/059 (`v0.v3-059`; IS +1.0894 / OOS +0.5791, 10-seed)
- Headline: IS monthly Sharpe +0.3993 / OOS monthly Sharpe +1.5458; 270 trades (177 IS / 93 OOS)
- IS daily Sharpe 1.0351 / OOS daily Sharpe 3.9292; OOS/IS daily ratio 3.7960 (inside [0.2,5] — SUSPICIOUS ratio leg does NOT fire)
- PBO 0.1276; frac_positive_paths 0.6444; n_eff 19; DSR 0.0 / PSR 1.0 / DSR_relative_b4 1.0
  (DSR/PSR EXPLORATION-mode artifacts — informational only)
- Falsifier cross-audit: **F2 FIRES** (IS +0.3993 < +0.60); F1/F3/F4 do NOT fire; F5 moot under precedence
- Classification: **EXPLORATION-NEGATIVE** (brief Section 8 LOCKED taxonomy step 2 — F2 fires); NO-MERGE; non-advancing
- `alpha032` disposition: **REVERTS** — `V3_FEATURE_COLUMNS_TOP_N` back to 14; `formulaic_v3.py`
  module + unit tests retained as infrastructure; `"alpha032"` joins the runner ABSENT-assertion ban
- WorldQuant Alpha#32 recorded as a dead idea (BASELINE_V3.md Dead Ideas + catalog) — documentation only
- Phase 5.5 gate SHA: `bc2a30a`; Phase 6 setup commit SHA: `556c345`
- EDA commit SHAs: `fd3165a` (WorldQuant-101 formulaic-alpha EDA — T1–T7) + `6b917f8` (alpha032 deep-dive — T8/T9/T10)
- Phase-7.5 Critic review: OVERALL=MERGE — no methodology BLOCK; Check 1 (Look-Ahead) PASS
- Diary SHA: (this commit)
- Catalog update SHA: (next commit — `briefs-v3/exploration_catalog.md` /102 row)
- BASELINE_V3.md Dead Ideas update SHA: (committed with the catalog)
- Tag: `v0.v3-102` — closeout marker only; BASELINE_V3.md baseline metrics UNCHANGED
- Library stack: UNCHANGED from /059 (Python 3.13, lightgbm 4.6.0, optuna 4.8.0, numpy
  2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1)
- Run command: `uv run python run_baseline_v3.py --exploration --n-trials 35 --clean-oof`
- NO CHEATING: `OOS_CUTOFF_DATE` / `training_months` untouched; QR saw OOS for the first
  time in Phase 7; all Phase 1–5 EDA verified IS-only; the Phase-7 cross-audit reads only
  committed report CSVs.
