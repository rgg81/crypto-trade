# PHASE C — CRITIC TOURNAMENT REVIEW (MN4, 10 reveals)

> Persisted VERBATIM by the orchestrator from the Critic's read-only Phase C review, 2026-07-12.
> Final verdict for Stage-3 routing. Multiplicity correction applied across all 10 reveals.

**Model:** Opus 4.8 (Fable rate-limited; user-directed per charter). Disclosed.
**Scope:** All 10 Phase-B reveals adjudicated together. Read-only. The verdict is final for Stage-3.
**Multiplicity lens applied:** Bonferroni (primary), Holm-Bonferroni (step-down confirmation), Benjamini-Hochberg FDR (q=0.10), Deflated Sharpe Ratio (Bailey-López de Prado, N=10, T=2yr). Frameworks disclosed and computed below; verdict does not hinge on choice.

---

## FINAL VERDICT — NO WINNER. No candidate proceeds to Stage-3.

The tournament **worked as designed**: 8/10 failed, the 2 PASSes split into one genuine-but-thin generalizer and one regime-coupled false positive, and the multiplicity correction — the entire reason a 10-idea tournament exists — kills the false positive and exposes the thin one. The user asked whether they have a real generalizer. The honest answer is **no**: they have a real *structural finding* (the trend/momentum family generalized across three independent constructions) but **no deployable all-weather book that clears a 10-way corrected significance bar.**

### Ranking (best-to-worst, by generalization quality not raw Sharpe)

| Rank | Idea | Holdout Sh | Verdict | Why this rank |
|---|---|---|---|---|
| 1 | **IDEA-10** ensemble | +0.445 | PASS (genuine, thin) | Only book whose alpha direction held cleanly w/o inversion or gate failure. Robustness real (maxDD shallower than every member). But t=0.63 — fails multiplicity significance. |
| 2 | **IDEA-01** TS-mom | +1.128 | FAIL (t=1.59) | Sharpe *improved* OOS, maxDD shallowed, crash flipped positive. Strongest raw generalization. Closed: gate was effectively a Sharpe≥1.41 bar on a 2-yr window (unreachable at +1.13). |
| 3 | **IDEA-03** regime | +1.094 | FAIL (mania-β) | Alpha held (−29.5% decay, normal), crisis defense fired on real unseen crashes. But mania-β +0.337 means headline Sharpe includes unhedged directional beta — attribution contamination, not just a "fixable flaw." |
| 4 | **IDEA-06** funding | +1.598 | PASS → **REJECT** | Raw Sharpe highest but IS-fail→holdout-pass inversion; model still worse than persistence baseline in *both* periods; win driven by aggregate funding-regime sign flip (4.4× income). Textbook multiplicity false positive. |
| 5 | IDEA-02 meta-breakout | +0.909 | FAIL | Real edge decayed; crash-fragile (−5.9); 2× cost kills it (+0.15). |
| 6-10 | 08, 04, 09, 05, 07 | neg | FAIL | Inversions (08, 04), nulls (09, 05), null-deepened (07). |

**IDEA-06 ranks 4th, not 1st, despite the highest raw Sharpe.** The pair's own self-diagnosis is conclusive; the multiplicity math finishes it. The Critic's correction exists precisely to prevent this book from being crowned.

---

## Per-candidate rulings

### IDEA-06 (PASS, suspect) → **MULTIPLICITY FALSE POSITIVE. REJECT.**

This is the hardest call the charter asks for, and the evidence is unusually clean.

**The pair's own forensics already made my case.** Five independent red flags, any one of which is disqualifying:

1. **IS-fail → holdout-pass inversion.** IS Sharpe −0.044 (1×) / −0.606 (2×). The model failed on the data it was tuned on. A book that cannot beat cost on 4.5 years of IS does not become a generalizer because it printed on the next 2.
2. **The model is still worse than a naive persistence baseline in both periods.** Persistence IC 0.5158 (IS) → 0.5389 (holdout); model IC 0.3715 → 0.3954. Δ identical at −0.14 in both. The model adds noise to a `-current_funding` ranking it cannot beat. A raw-carry book would have scored higher.
3. **The win is a single macro covariate flipping sign.** Aggregate funding mean: +6.92e-5 (longs pay shorts, IS) → −3.56e-4 (shorts pay longs, holdout). Std 2.7× larger; absolute carry 1.77×; per-candle funding income 4.4×. The short-biased `-pred_mean` signal earned carry in holdout it paid in IS. That is not prediction alpha; it is leveraged bear-regime carry.
4. **The headline rests on small-sample regime buckets.** CRASH n=246 (11.2%), MANIA n=109 (5.0%). The 80%-occupancy CHOP Sharpe is +1.33 — the only reliable number, and it trails IDEA-01/03/10-mothers' CHOP. The +1.60 headline is propped up by ~355 favorable-but-noisy regime candles.
5. **Regime tells everywhere.** Crisis throttle ΔSharpe flipped +0.146 → −0.287. ETH-armed hedge rebals 0 → 80. The holdout regime is structurally different from IS, and the book's PnL is dominated by that covariate.

**Multiplicity math (the finisher).** The pair flagged "one PASS out of 10 at +1.6 is right at the expected false-positive rate." The math confirms:

- **t-statistic on 2-year holdout:** t = 1.598 × √2 = **2.26** (p ≈ 0.024, two-tailed).
- **Bonferroni** (N=10, α=0.05): per-test α'=0.005, z_crit=2.81. **2.26 < 2.81 → FAIL.**
- **Holm-Bonferroni:** smallest p in the family (0.024) vs first-step threshold 0.005 → fail. Step-down stops. **Zero survivors.**
- **BH FDR (q=0.10):** rank-1 threshold (1/10)×0.10 = 0.01. p=0.024 > 0.01. **Zero discoveries.**
- **Deflated Sharpe (LdP):** SR_min ≈ √(2·ln 10)/√2 ≈ **1.52** at N=10, T=2yr. IDEA-06's 1.598 is borderline — *but DSR assumes the holdout is sampled from the same distribution as IS, which the pair just proved false.* Adjusting for the regime flip, the "true" Sharpe is the IS value (−0.04) plus a single-shot carry-regime lottery ticket, not 1.60.

**Adjudication:** IDEA-06 is a regime-coupled carry book that scored on a bear-regime holdout by accident of the funding sign flipping. It is not a generalizer. It is the textbook case the Phase-C Critic exists to catch. The frozen gates PASS (4/4), the mechanical verdict is PASS, but the Phase-C verdict is **REJECT as a multiplicity false positive.** The pair's own honesty is what makes this call defensible.

---

### IDEA-10 (PASS, genuine candidate) → **GENUINE PARTIAL GENERALIZER, BUT FAILS MULTIPLICITY-CORRECTED ECONOMIC RELEVANCE. NO STAGE-3.**

Everything that could hold, did hold. I credit this honestly:

- Composite Sharpe +0.445 held from IS +0.496 (cost-surviving at both 1× and 2×-GT).
- **Diversification-as-design generalized:** holdout maxDD −36.3% shallower than *every* member (best member −44.3%, worst −97.2%). This is the real, bankable result.
- β-neutral maintained (median β_BTC −0.025).
- Two strong sleeves (`ts_mom90` +0.93→+1.10, `carry21` +1.25→+1.46) — canonical crypto edges confirmed OOS.
- 3 of 4 halves positive. No blow-up half.

But the pair's own anti-spin section is also conclusive on why this does not clear a deployment bar after a 10-way haircut:

1. **Sharpe +0.445 over 2 years gives t = 0.445 × √2 = 0.63 (p ≈ 0.53).** This is *indistinguishable from zero even before multiplicity correction.* After Bonferroni/Holm/BH it is a flat non-discovery. DSR wants ≥1.52; the book is at 0.45.
2. **Two of four members are structural drags** (`reversal21` −1.65, `ownvol90` −0.50). The composite trails the best member (`carry21` +1.46) by a full Sharpe point. The pair correctly notes the ensemble's value proposition is *risk control, not return* — but a Sharpe of 0.45 is too thin to spend the optionality of Stage-3 on.
3. **The IS crash-failure (−1.005) → holdout crash-success (+2.22) is itself a regime inversion.** The pair flagged this honestly: "this does NOT prove the construction is crash-robust in general — it proves the holdout's crash episodes happened to be friendlier." A different holdout could reproduce the IS crash loss. The 2025-H2 half (−0.91) is the tell that the book is not immune.
4. **The 2× > 1× Sharpe quirk (+0.487 > +0.445) is a throttle path artifact**, disclosed by the pair. Not cost-defiance; just dd_brake firing at a luckier equity path.

**Adjudication:** IDEA-10 is the tournament's strongest *robustness* profile and its only honest generalizer. It clears the frozen gates. It does **not** clear the multiplicity-corrected economic-relevance floor that a Phase-C Critic must apply. A 6-month Stage-3 paper trade would confirm what the t-statistic already tells us: a weak, robust, sub-significance signal. That is not what Stage-3 is for. **No Stage-3.**

---

### IDEA-01 (FAIL, t-stat gate) → **GATE FAILURE IS BINDING. ALPHA GENUINELY HELD. CLOSED.**

The strongest raw generalization in the tournament — and the clearest case of a gate that was miscalibrated to the sample length.

- Sharpe *improved* +0.963 → +1.128 (rare).
- maxDD *shallower* −34.4% → −26.4%.
- CRASH *flipped* from structurally negative (−0.916) to mildly positive (+0.255). The pair's Phase-A "CRASH is structurally negative" read was IS-specific, not structural.
- Cost coverage 159× → 174×. Cost is non-binding.
- The only regression: t-stat 1.987 → 1.594.

**The gate-design problem.** Gate-F required t > 2.0. On a 2-year holdout, t = Sharpe × √2, so t>2.0 requires Sharpe ≥ 1.414. IDEA-01's Sharpe of +1.128 was *mathematically unreachable* for the gate as frozen. This is not a strategy failure; it is a gate calibrated to a longer sample. **Lesson for MN5, not a reason to re-open this construction.**

**Adjudication:** The charter is explicit — *"Terminal per construction: PASS → candidate / FAIL → closed."* Frozen-gate discipline is load-bearing. If the Critic re-opens gate-failed constructions because "the alpha held," every future pair will tune to the Critic's soft spot and the tournament design collapses. **FAIL is FAIL. IDEA-01 is closed.** Its token is spent; its trend-family edge is banked as a structural finding.

---

### IDEA-03 (FAIL, mania-β gate) → **GATE FAILURE IS BINDING. ALPHA HELD WITH ATTRIBUTION CAVEAT. CLOSED.**

Alpha held: Sharpe +1.552 → +1.094 (−29.5% decay, normal regime-decay range), 2× cost survives at +0.924, crisis defense fired on real unseen crashes (Aug-2024 yen-carry, Oct-2025 deleveraging — 4 distinct CRISIS entries caught at 0-lag), STRESS blue-chip contraction earned Sharpe +1.54.

But the mania-β failure is **more substantive than "one narrow gate."** MANIA β_BTC = +0.337 with +2424 bps earned in 109 mania candles. During mania, everything pumps together, the cross-sectional momentum signal correlates with BTC direction, and the hedge overlay can't cancel it. The mania gains are **unhedged directional beta profit**, not cross-sectional alpha. On this holdout (the mania was bullish), that beta was a gift; on a mania-that-crashes, the same β+0.34 would be a catastrophic bleed. The gate is principle-anchored exactly for this reason: |β|<0.20 in every bucket, because a book that earns from unhedged beta in one regime is structurally short volatility of the hedge.

**Adjudication:** This is not a "fixable construction flaw" — it is a signal that the headline Sharpe is attribution-contaminated. Removing the mania beta (which the gate enforces) might remove the mania alpha (which drove the +1.094). The pair's "fixable flaw" framing is too generous. **FAIL is FAIL. IDEA-03 is closed.** The regime-adaptive crisis-defense primitive, however, is a bankable structural positive — it demonstrably fired on unseen stress.

---

## The multiplicity framework (applied)

**Family:** 10 ideas, one PASS criterion each, tested on the same 2-year holdout. Trial correlation is non-trivial (shared universe, data, cost model, hedge overlay) so N_eff < 10 — but the verdict is robust to N_eff assumptions.

| Candidate | Holdout Sh | t = S·√2 | p (2-tail) | Bonf (α'=0.005) | Holm step-1 | BH q=0.10 | DSR (SR_min≈1.52) |
|---|---|---|---|---|---|---|---|
| IDEA-06 | 1.598 | 2.26 | 0.024 | FAIL | FAIL | FAIL | borderline* |
| IDEA-01 | 1.128 | 1.59 | 0.111 | FAIL | — | FAIL | FAIL |
| IDEA-03 | 1.094 | 1.55 | 0.122 | FAIL | — | FAIL | FAIL |
| IDEA-10 | 0.445 | 0.63 | 0.530 | FAIL | — | FAIL | FAIL |
| IDEA-02 | 0.909 | 1.29 | 0.198 | FAIL | — | FAIL | FAIL |

\* IDEA-06's DSR borderline is **invalidated** by the regime-flip diagnosis — DSR assumes IS/OOS same distribution, which REVEAL-06 disproved.

**Corrected PASS count: 0.** Family-wise error rate controlled at α=0.05 across the tournament. The two nominal PASSes (06, 10) both fail to survive any defensible correction. This is not a close call at the framework level — it is only "close" in the sense that IDEA-06's raw Sharpe is high; once the t-statistic is computed and the regime diagnosis is weighted, the verdict is decisive.

**Robustness to N_eff:** even at N_eff=5 (charitable — the 10 ideas are diverse in mechanism even if they share plumbing), Bonferroni z_crit drops to 2.58. IDEA-06's t=2.26 still fails. IDEA-10's t=0.63 fails catastrophically. The verdict is unchanged.

---

## "Winner in every market" assessment — **NONE**

The charter target is a strategy that wins in *every regime* (bull/bear/chop/crash/mania). I assess each plausible candidate's per-regime profile against this bar:

- **IDEA-10:** CHOP Sharpe +0.198 (the 80%-occupancy regime — the only reliable number). MANIA +0.44 (n=109, thin). CRASH +2.22 (small-sample + pair-flagged regime-specific). 2025-H2 −0.91. **Not all-weather** — bled in 2025-H2, modest in chop. The robustness is real; the "every market" claim is not.
- **IDEA-06:** Lost badly in IS CRASH/MANIA (−1.57, −1.48), won in holdout CRASH/MANIA (+4.41, +4.39, small samples). **Regime-dependent, not all-weather** — the IS losses *are* the evidence that this book is not winner-in-every-market; it lost in the IS instances of the same regimes it won in on holdout. The "all-weather" framing is impossible for a regime-coupled carry book.
- **IDEA-03:** Crisis defense worked (good), but mania-β +0.34 means the book is *net-long BTC during manias* — that is the opposite of market-neutral all-weather. **Not all-weather.**
- **IDEA-01:** CRASH flipped positive (+0.255), CHOP +1.27 (carried), MANIA +0.71 (thin, n=109). The closest thing to all-weather in the field, but the t-stat gate failure and thin mania sample mean we cannot confirm it. **Candidate-not-confirmed.**

**Verdict on the mandate:** zero candidates meet the "winner in every market" bar, even loosely. The honest read is that the trend/momentum *family* showed the most consistent cross-regime resilience, but no construction cleared the deployment bar in every regime.

---

## STAGE-3 RECOMMENDATION — **NONE. HERE IS WHY AND WHAT INSTEAD.**

**No Stage-3 paper trade for any MN4 candidate.** Reasoning:

- The 2-year holdout already told us what 6 months of forward paper would tell us for the two PASSes: IDEA-10's Sharpe is indistinguishable from zero (t=0.63), and IDEA-06's pass is a funding-regime flip artifact. Stage-3 is the user's last pristine forward arbiter; spending 6 months of it on a sub-significance robustness book or a regime-lottery carry book wastes the optionality.
- The two narrow-gate FAILs (01, 03) are closed by charter rule; reopening them for Stage-3 would retroactively convert the tournament from "frozen-gate terminal" to "Critic-discretion terminal," which destroys the methodology that made the trend-family signal credible in the first place.
- The honest finding is the tournament *worked* — it produced a clean structural signal and refused to certify a false positive. That is a successful null-plus-structural result, which the charter explicitly endorses: *"A FAIL on the holdout is the methodology working, not a disappointment."*

**What instead — the tournament's actual value is the structural output, bank it:**

1. **Trend / time-series momentum generalized across three independent constructions** (01 TS-mom, 03 regime-mom, 10's `ts_mom90`/`carry21` members). All held or improved OOS through real unseen crashes. The canonical quant all-weather prior is real on crypto at weekly/daily cadence, beta-hedged. **This is the tournament's headline finding.**
2. **BTC-only minimal-L2 beta projection generalized cleanly** across the entire field (10/10 books). Neutrality-by-construction is a solved primitive in this track.
3. **ML cross-sectional residual-alpha does NOT generalize through regime shifts** — IC held (+0.05, t+11.8 on IDEA-04) while the long-short spread inverted in crashes (+33% → −192%). Confirmed for the second time (MN3-G-SLOW was the first). The ranking-to-return relationship is regime-dependent: 2020-24 retail flow and 2024-26 ETF/institutional flow have *opposite* crash cross-sectional structure. ML flagship is dead as a book, alive as a ranking signal — a different extraction layer (spacing/options rather than equal-rank demeaned weights) might rescue it.
4. **Funding carry is regime-coupled, not a free all-weather premium** (6th confirmation). It pays in bear/liquidation regimes (holdout −3.6e-4 aggregate) and bleeds in bull/mania regimes (IS +6.9e-5). IDEA-06's "win" is this covariate, not funding-prediction alpha.
5. **Static directional managed-variance bleeds in chop** (IDEA-08). Vol-targeting handles sharp crashes (CRASH improved −43.8% → −23.8%) but cannot exit downtrends; long-only + vol-target is just a de-risked long that bleeds to −82.8% over a choppy 2-year holdout. Directional all-weather *requires a trend EXIT, not just de-risk*.

---

## Path Forward — the MN5 implication (advisory)

The tournament points unambiguously at the next construction. If the user charters an MN5, the empirically-grounded move is to **build ONE focused trend/carry ensemble** — not run another 10-way tournament:

1. **Core:** TS-mom (IDEA-01's signal, weekly) + short-tenor funding carry (IDEA-10's `carry21` member) — both confirmed OOS across independent constructions.
2. **Risk layer:** regime-adaptive crisis defense (IDEA-03's detector, which fired on real unseen crashes) + BTC/ETH hedge overlay (field-validated).
3. **Drop the drags:** no reversal (confirmed negative twice), no own-vol-tilt (confirmed negative), no static managed-variance long-only (chop-bleed), no ML residual-alpha at the book level (crash inversion twice-confirmed).
4. **Gate design lesson:** set gates that are *achievable on the sample length.* A t>2.0 gate on a 2-year holdout is a Sharpe≥1.41 gate; if the economic-relevance floor is Sharpe 1.0, gate on Sharpe 1.0 and use DSR/PBO for the multiplicity lens.

That is a single sharp construction built from the tournament's bankable positives, and it is what I would recommend the user authorize next — as a new IS→holdout build on a future pristine holdout window, **not** as a Stage-3 forward test of an MN4 candidate (the MN4 tokens are spent; the MN4 holdout is contaminated for any MN5 derivative of these constructions).

---

## Bottom line for the user

You ran a 10-idea blind tournament with a 2-year sealed holdout. The methodology worked. You got one genuine-but-thin generalizer (IDEA-10), one regime-coupled false positive that the multiplicity correction caught (IDEA-06), two narrow-gate FAILs whose trend/momentum alpha genuinely held (01, 03), and a clean cluster of confirmatory nulls/inversions that bank real structural findings. **You do not have a deployable all-weather generalizer.** You have a confirmed family (trend/mom + carry + BTC-L2 neutrality + regime-adaptive crisis defense) that is the right substrate for the next build. That is the honest, multiplicity-corrected answer, and it is the answer the tournament was designed to produce.

**Stage-3: none. Winner: none. Structural findings: banked. Next move: a focused trend/carry ensemble on a new pristine holdout, if the user charters it.**

---

*— Quant Critic, Phase C, MN4 tournament, 2026-07-12. Read-only. Multiplicity correction applied across all 10 reveals. Verdict final for Stage-3 routing.*
