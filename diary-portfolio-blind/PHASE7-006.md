# PHASE7-006 — EXPLORATION-006 IS gate evaluation + FROZEN verdict

**Date:** 2026-07-10. **IS Verdict: SUCCESS-WITH-CAVEATS** (adopting Critic REVIEW-006's tier verbatim).
**Tree-resolved primary candidate: L1 (C1 + C2).** All 7 HARD + all 5 SOFT gates pass → frozen §5.5
interpretation map lands in the **SUCCESS tier**; the Critic's eight mandatory caveats bar
"SUCCESS-CONFIRMED" and are carried in full below.

**This is an IS design-validation, NOT a deployability claim. There is no OOS reveal in this phase**
(the /005 base already burned the one-shot OOS look; `OOS_CUTOFF = 2025-03-24` sealed; `CONFIRMATION-005.md`
not read). Every number below is IS-only. Engineer scope was respected (observations only); this
document renders the gate verdicts, the §5.2 tree resolution, and the §5.4 paragraphs.

---

## 1. Decision-tree resolution (frozen §5.2) → candidate = L1

Ladder marginals (from the engineering matrix, frozen warmup=63 slice):

| marginal | ΔSharpe | ΔMania (pp) | ΔCrash (pp) |
|---|---|---|---|
| m_C1 = Sh(V1)−Sh(V0) | +0.0918 | +1.431 | −0.318 |
| m_C2 = Sh(L1)−Sh(V1) | +0.1586 | +1.874 | −0.515 |
| m_C3 = Sh(L2)−Sh(L1) | −0.1805 | −1.906 | −0.147 |
| m_C4 = Sh(L3)−Sh(L2) | −0.2472 | −1.375 | −0.442 |

Applying the frozen §5.2 drop rules, top-down, prefer-lean:

- **Drop C3 (R2 — unambiguous):** `m_C3 = −0.1805 < −0.05` **AND** `ΔMania_C3 = −1.906pp ≤ 0` → first
  bracket TRUE. The pinned crash-preservation clause **did NOT fire**: `crash(L2) = +1.607%/mo ≥ +1.55%`
  (the leanest stack containing C3, per the F3 pin), so C3 is dropped on the Sharpe+mania bracket, not
  the crash bracket. → fall back to **L1**.
- **Drop C4 (by nesting):** C4 can be IN the stack only if C3 is IN; C3 is dropped, so C4 drops by
  construction regardless of R1. (Its own marginal was also negative: `m_C4 = −0.2472`, `ΔMania_C4 =
  −1.375pp`; its one virtue was tightening maxDD −28.45% → −25.67% and turnover 48.0x → 40.8x.)
- **Retain C2 (R3 not triggered):** `m_C2 = +0.1586 ≥ −0.05` — C2 lifts both Sharpe and mania, so it
  stays.
- **C1 never dropped** (the anchor).

**⇒ Primary candidate = L1 (C1 + C2).** The lean end of the ladder (the two surgical short-leg
controls) is exactly the pair the frozen tree retains; the two symmetric/stateful governors (C3, C4)
are correctly shed.

**Erratum — Rule-1 escape-clause sign error (Critic F1; non-dispositive, fix before any reuse).** The
frozen Rule 1 reads "Drop C4 iff `m_C4 < −0.05` AND C4 does not tighten maxDD by ≥1pp
(`maxDD(L3) ≥ maxDD(L2) − 0.01`)." The parenthetical formula is inverted relative to its gloss: with
maxDD stored as a negative number, "does not tighten by ≥1pp" is `maxDD(L3) < maxDD(L2) + 0.01`, not
`≥ maxDD(L2) − 0.01` (the as-written form is nearly always TRUE, since a *tightening* C4 makes
`maxDD(L3) > maxDD(L2)`). Here C4 *did* tighten maxDD by 2.78pp, so under either reading Rule 1's
maxDD clause is not what keeps C4 — **nesting governs** and the candidate is L1 unchanged. The erratum
is recorded for any future reuse of the tree; it did not affect this phase's resolution.

---

## 2. Gate scorecard for L1 (frozen §4) → SUCCESS tier

| # | Gate | Type | Threshold | L1 observed | Verdict |
|---|---|---|---|---|---|
| G-years | per-year Sharpe all ≥ 0 | HARD | every year ≥ 0 | min-PY **+0.10** (2023) | **PASS** |
| G-crash | crash-bucket mean | HARD | ≥ +1.55%/mo AND > 0 | **+1.754%/mo** | **PASS (thin, +0.20pp)** |
| G-mania | mania-bucket mean | HARD | ≥ +4.52%/mo | **+5.829%/mo** | **PASS** |
| G-sharpe-floor | Sharpe / 2×-cost | HARD | ≥ +0.45 AND ≥ +0.35 | **+1.164 / +1.028** | **PASS** |
| G-dd-floor | maxDD | HARD | ≥ −35% | **−28.58%** | **PASS** |
| G-turnover | turnover ann | HARD | ≤ 100x | **50.1x** | **PASS** |
| G-worst-month | worst calendar month | HARD | ≥ −15.0% | **−12.72%** | **PASS** |
| G-crash-win | crash win rate | SOFT | ≥ 55% | **70%** | PASS |
| G-crash-leg | crash aggregate short_px | SOFT | > 0 | **+1.373** | PASS |
| G-mania-worst | mania worst month | SOFT | better than V0's −16.35% | **−10.63%** | PASS |
| G-sharpe-target | Sharpe / 2×-cost | SOFT | ≥ +0.60 AND ≥ +0.50 | **+1.164 / +1.028** | PASS |
| G-dd-target | maxDD | SOFT | ≥ −30% | **−28.58%** | PASS |

**All 7 HARD + all 5 SOFT pass.** Per the frozen §5.5 map, SUCCESS requires all 7 HARD gates AND both
SOFT Sharpe targets (≥ +0.60 / ≥ +0.50) AND the SOFT maxDD target (≥ −30%) — all satisfied. **⇒ SUCCESS
tier.** The goalpost is not moved: these are the thresholds frozen in the brief before the run, and the
candidate is the rule-selected stack, not a post-hoc pick.

---

## 3. §5.4 mandatory verdict paragraphs

**(a) C5 falsification arm — diagnostic thesis AFFIRMED.** C5 (whole-book BTC-drawdown de-gross) was
pre-registered to HURT. It did, on every axis: **Sharpe(V5) +0.842 vs Sharpe(V0) +0.913 (Δ −0.072)**;
**crash-bucket +1.492%/mo vs V0 +2.586%/mo (−1.094pp)** — the whole-book cut ate the crash short leg
(short_px +1.531 → +0.974, −36%); **mania Δ −0.292pp (≈ 0)** — BTC-up mania sees little BTC drawdown, so
C5 does nothing where the real problem lives. All three moves are in the pre-registered NEGATIVE
direction. **This affirms DIAGNOSTIC-003's central thesis: BTC-crash de-risking attacks the WRONG
regime; the short leg IS the crash alpha and must not be cut.** No observation shows C5 improving Sharpe
or the crash bucket. C5 stays OUT of the stack (falsification only), as frozen.

**(b) C1 anchor — validated.** C1 was pre-registered to improve the mania bucket (`ΔMania_C1 > 0`).
Observed: **mania(V1) +3.955%/mo vs mania(V0) +2.524%/mo → ΔMania_C1 = +1.431pp > 0**, driven by cutting
the squeezed short leg (short_px −1.912 → −1.665). The lead mechanism did what the diagnostic said it
would; the anchor is validated and correctly non-droppable.

---

## 4. Verdict: SUCCESS-WITH-CAVEATS — the eight mandatory caveats (carried in full)

The IS tier is SUCCESS; the deployment reading is **SUCCESS-WITH-CAVEATS** (Critic REVIEW-006, adopted
verbatim). The eight caveats are load-bearing and travel with any downstream use of L1:

1. **IS design-validation ONLY — no deployability claim.** L1 is validated in-sample against frozen
   gates; a separate forward-validation on genuinely unseen data is MANDATORY before any deployment.
2. **Deflate the headline.** L1's +1.164 Sharpe is an **IS UPPER BOUND**. Phase n_eff ≈ 5–6, cumulative
   ≈ 15–21, plus the un-counted C2-threshold DOF and the second-IS-redesign-after-burned-OOS
   compounding → **honest forward expectation ≈ +0.75–0.95, a wide band.** Do not quote +1.164 as an
   expected live Sharpe.
3. **G-mania is a MECHANISM-EFFICACY test, not independent regime alpha.** The 13-month bucket is
   C1's own firing footprint: 12 of 13 are short-loser months where C1 helps by construction, and
   **only 2020-12 (short_px +0.143) is a genuine short-leg-winner where C1's floor-0.5 clip HURTS.**
   G-mania passing (+5.83 ≥ +4.52) means the stack net-improves its own footprint after C3 de-gross /
   C2 shrink / turnover — it is NOT evidence of alpha on an independently-defined regime. **Erratum:
   the engineering report §7(iii) repeats the retired winner-clip miscount (it cites 2024-02, whose
   short_px is −0.041 → C1 HELPS, as a clip-hurts month); PHASE7-006 supersedes with the corrected
   2020-12-ONLY framing. Do not inherit the §7(iii) 2024-02 slip.**
4. **G-crash margin is THIN (+0.20pp) with a materialized erosion mechanism.** crash(L1) = +1.754%/mo
   clears the +1.55% floor by only 0.20pp. The named OOS risk (Critic F2, engineering §9.4): **C1 fired
   30% in 2022-08 — a BTC-DOWN capitulation month where the short leg was WINNING (V0 short_px +0.065)**
   — because an intra-month bear rally pushed `btc_mom_63 > +9%`. This is the 2022-07→08 turn that
   RISK-006's tail scenario (2021-04→05 only) never examined. The erosion is small IS but is a real
   forward crash-robustness risk on any capitulation with an embedded bear rally.
5. **C2 is the FRAGILE contribution.** Its lift is real in direction (excluded parabolic shorts had
   −4.08 forward short_px; sparse at 5.6% of short-name-candles) but **inflated and 2024-11-concentrated
   — ~+4.8pp of the mania improvement lands in 2024-11, the exact month Q=+0.30 was audited against
   (a tailoring signature).** Q=+0.30/K=21 is a single un-scanned, P&L-adjacent point. **No post-hoc Q
   scan is permitted on this burned IS window; forward-validation MUST stress C2 on non-2024-11
   squeezes.** Deflated C2 forward contribution ≈ +0.10–0.15 (vs +0.16 IS).
6. **The mania fix rests on C1 + C2 (surgical past-only market-signal controls); C3 + C4 were
   correctly dropped.** C1/C2 are well-calibrated (3-of-3 predictions HIT each); C3 (symmetric
   vol-target) and C4 (stateful DD brake) are mis-calibrated governors. **C4 stickiness lesson:** on
   the actually-braked equity C4 sat braked for **76/273 rebal steps (28%)** vs RISK-006's un-braked
   estimate of ~4 episodes / ~16% of candles — halved gross slows recovery to the −10% release, so the
   brake locks out the rebound (RISK-006 §4.1's own caveat materialized). Recalibrate C4 on the
   braked-path feedback before any re-introduction; do NOT re-add it on the descriptive calibration.
7. **Both §5.4 paragraphs are recorded** (§3 above): C5 falsification NEGATIVE on all axes (thesis
   affirmed) + C1 anchor validated (ΔMania_C1 +1.431pp).
8. **Fix the Rule-1 escape-clause sign error** (§1 erratum) before any future reuse of the decision
   tree. Non-dispositive here (nesting governs); a latent bug otherwise.

---

## 5. What the phase delivered vs the user directive

User directive: *"succeed in ALL market conditions, ESPECIALLY the worst price-drop months; keep all
IS years positive; a decent Sharpe is fine, need not be 0.91."* L1 (C1+C2) against V0 (/005), IS-only:

| dimension | V0 (/005) | **L1 (C1+C2)** | read |
|---|---|---|---|
| all IS years/part-years ≥ 0 | yes (min +0.35, 2023) | **yes (min +0.10, 2023)** | mandate met — but 2023 thinned +0.35 → +0.10 (the trade-off) |
| crash bucket (20 mo, worst price-drops) | +2.586%/mo, 70% win | **+1.75%/mo, 70% win** | preserved as a net winner (short leg still the crash friend, short_px +1.373) |
| mania bucket (13 mo) | +2.524%/mo | **+5.829%/mo** | the redesign's target — FIXED (+3.3pp) |
| worst single month | −16.35% (2024-11) | **−12.72%** | +3.6pp better |
| maxDD | −32.99% | **−28.58%** | +4.4pp tighter |
| top-10-month concentration | 98.8% | **83.0%** | materially less fat-tail-fragile |
| headline Sharpe / 2×-cost | +0.913 / +0.771 | **+1.164 / +1.028** | ABOVE V0 |

**The phase over-delivered on the directive's letter:** all six IS years stay positive, the crash
months remain a net winner, the mania squeeze is fixed, drawdown depth and concentration both improve,
and the headline Sharpe went **UP** rather than taking the pre-authorized haircut. **Two honest
qualifications:** (i) the 2023 part-year Sharpe thinned from +0.35 to +0.10 — the weakest regime got
weaker even as the aggregate improved, so "all years positive" holds by a thinner margin; (ii) **per
caveat 2, the +1.164 headline is an IS UPPER BOUND** — the honest forward expectation is ~+0.75–0.95,
and the crash margin (+0.20pp) and C2's 2024-11 concentration are the specific places that band could
bite. The directive is met in-sample; the "decent Sharpe is fine" latitude was not even needed IS, but
is exactly the cushion the deflation consumes.

---

## 6. Named next step (NOT started here)

**Forward-validation protocol for the frozen L1 (C1+C2) construction.** The one-shot OOS look on the
/005 base is spent (CONFIRMATION-005), so IS-window OOS cannot re-validate L1 — validation must come
from **genuinely unseen forward data** (e.g., paper-trading the byte-frozen L1 construction on
post-cutoff live candles, or a fresh held-out window that never informed C1/C2/the mania rule). The
protocol must, per the caveats: (a) treat +0.75–0.95 as the expectation band, not +1.164; (b) stress
C2 on **non-2024-11** squeezes; (c) watch the thin crash margin on any capitulation-with-bear-rally
(the 2022-08-type C1 mis-fire); (d) keep C3/C4 OUT unless C4 is first recalibrated on braked-path
feedback. **This is named as the follow-on only — it is NOT designed or run in this phase.** No OOS was
touched here.

---

**FROZEN VERDICT: SUCCESS-WITH-CAVEATS.** Primary candidate L1 (C1+C2) clears all 7 HARD + all 5 SOFT
frozen gates (SUCCESS tier), the C5 falsification affirms the diagnostic thesis, and the C1 anchor is
validated — but the result is an **IS design-validation, not a deployable book**: the +1.164 headline
deflates to a ~+0.75–0.95 honest forward expectation, G-mania is mechanism-efficacy (not regime alpha),
the crash margin is thin, and C2 is the fragile, 2024-11-concentrated contribution that a mandatory
forward-validation must stress before any deployment.
