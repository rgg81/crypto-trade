# PHASE7-A3 — QR Formal Verdict on EXPLORATION-A3 (family A TERMINAL; MN track)

**Date:** 2026-07-10 · **Role:** Quant Researcher (Phase 7 IS evaluation) · **Track:** baseline-BLIND
MARKET-NEUTRAL (MN). **Contract scored:** `briefs-portfolio-mn/EXPLORATION-A3.md` (frozen da980cc2)
+ PRE-RUN AMENDMENT 001 (C1–C4). **Inputs:** `EXPLORATION-A3-engineering.md` (QE observed values),
`REVIEW-A3.md` (Critic). **Holdout SEALED and unspent; no OOS touched; no construction change here.
This is family A's TERMINAL attempt — shelve-on-fail, no A4.**

---

## 1. TIER — plainly: **SUCCESS (in the pinned MARGINAL disposition)**

Frozen §5 map: **all 11 HARD gates PASS on unseen numbers → TIER = SUCCESS.** Family A's FIRST
all-HARD-pass. A3-1 becomes **THE family-A holdout-reveal CANDIDATE** — presented per the C3-pinned
MARGINAL disposition WITH the explicit <3pp-fragility warning and the QR weak-basis note. **The
reveal is NOT spent here (USER-only, and per §5 below the USER has decided HOLD).**

### Gate scorecard (verdicts rendered; QE left them blank per scope) — A3-1

| gate | observed | frozen threshold | verdict |
|---|---|---|---|
| G1a (H) | within 97.2%, max 0.1760 | ≥95% \|β_BTC\|≤0.10 AND max ≤0.20 | **PASS** (unchanged-to-better vs A2's 97.0%/0.1813) |
| G1b (H) | within 100.0%, max 0.0913 | ≥95% \|β_ETH\|≤0.15 AND max ≤0.25 | **PASS** |
| G2-CRASH (H) | β +0.0094 (n=658) | \|β\| ≤ 0.15 | **PASS (beta-honest, no hedge leg)** |
| G2-MANIA (H) | β −0.0112 (n=999) | \|β\| ≤ 0.15 | **PASS** |
| G3 (H) | rebal-row max 0.0699 (executed ≤2.39e-15) | ≤ 0.10 at every rebal | **PASS** (bit-equal to A2 by scale-invariance) |
| G4 (H) | worst-bucket t +0.71 (CRASH) | t > −1.0 | **PASS** (crash t≈0 = neutrality delivered) |
| G5 (S) | max bucket share 69.8% (CHOP) | no bucket > 60% | SOFT-FAIL (expected/disclosed) |
| G-sharpe-floor (H) | +1.7341 | ≥ +0.35 | **PASS** |
| G-sharpe-target (S) | +1.7341 | ≥ +0.90 | PASS |
| G-durable (H) | 6/6 yrs > 0 (drip Sharpe informational) | ≥ 5/6 years positive | **PASS** |
| G-2xcost (H) | +1.5107 (0.87×) — GROUND TRUTH | > 0 AND ≥ 0.5×(1×) | **PASS** |
| G-2xcost-target (S) | +1.5107 | ≥ +0.60 | PASS |
| **G-maxdd (H)** | **−23.11%** | ≥ −25% | **PASS (margin +1.89pp ≈ 1.25 noise-units)** |
| G-maxdd-target (S) | −23.11% | ≥ −15% | SOFT-FAIL |
| G-turnover (H) | 52.3× | ≤ 250×/yr | **PASS** |
| G-sample (H) | ≥285 rebals/tranche; 352 names | ≥200 AND ≥40 | **PASS** |
| G-contam (S) | ex-window +2.1432 = 1.24× full | ≥ 0.7× full-IS | PASS |

**§3.1 bin (C3 pinned, applied):** maxDD **−23.11% ∈ (−25%, −22%]** AND Sharpe **+1.7341 ≥ +1.30**
→ **MARGINAL.** The frozen G-maxdd gate PASSES (+1.89pp margin), so the TIER is SUCCESS and A3-1 is a
reveal CANDIDATE — but the pass clears −25% by **+1.89pp ≈ 1.25 noise-units** (family noise ~±1.5pp)
and MISSES my own −22% noise-robust "worth-it" bar by **0.89pp**. Per C3 (pre-pinned, not tailored):
NOT auto-reveal, NOT shelve — candidate presented WITH the <3pp-fragility warning and the standing QR
note that **a fragile re-pass is a WEAK basis for spending the one-per-family-FOREVER holdout.**

---

## 2. §3.1 FALSIFIER sign-slip ERRATUM (dated 2026-07-10, ratified — Critic Ruling 1)

My frozen §3.1 FALSIFIER line reads "maxDD ≥ −25%" — a **sign-convention slip**. The internally-
consistent reading, uniquely pinned by the §3.1 MARGINAL interval `(−25%, −22%]` and the §4 G-maxdd
gate (`≥ −25%` = pass), is: **FALSIFIER = maxDD WORSE than −25% (i.e., maxDD < −25%, deeper).**
ERRATUM recorded; the mechanical bin applied the corrected reading. **Zero effect on the verdict:**
the tier is gate-driven, the gate passed at −23.11%, and the boundary is consistent (at ~−26% the
gate would FAIL and the falsifier would fire together). Precedent: the A2 degenerate-guard erratum,
same disposition (documentary correction, no result change).

---

## 3. The family's DURABLE result — mechanism validated (recorded)

Independent of the fragile NUMBER, the SCUD throttle's MECHANISM is validated beyond doubt, and this
is the bankable finding:

- **Episode alignment 4/4 FIRED, timing 2 LEAD / 2 COINCIDENT / 0 LAG** — no "fired-at-the-trough,
  aligned-but-useless" LAG signature.
- **Clip ∝ timing:** the two LEAD episodes get material clips (+1.20pp / +1.41pp of monthly return),
  the two COINCIDENT ones small partial clips (+0.09pp / +0.22pp). The throttle fires early where it
  matters.
- **Clipped IN PLACE:** maxDD is the SAME 2023-09-27→2024-03-09 grind in both books (identical peak/
  trough dates); the throttle shaved **2.46pp** off the shared path (−25.57% → −23.11%) rather than
  displacing the drawdown elsewhere.
- **Sharpe-ACCRETIVE (ratio 1.033):** the throttle did not tax Sharpe — it added to it. Decomposition
  (§9.3): return-neutral (−0.10 bps/cd), vol −1.25pp; inside active windows loss-averted +0.7734 vs
  carry-foregone −0.8387 — de-risking landed on ~zero-alpha, high-variance windows.
- **Structural proof: throttled weights = s·(A2 weights) at 8.33e-17** → neutrality by scale-
  invariance (G1a/G2/G3 unchanged-to-better, verified as gates).

**Framing (adopted from Critic Ruling 2): fragile NUMBER, robust MECHANISM.** The bankable claim is
"the SCUD throttle clips the squeeze tail for free in Sharpe." The fragile claim is "IS maxDD clears
−25% with margin." I do NOT conflate them: the mechanism is the durable family-A result; the specific
−23.11% is a noisy boundary number that will likely deepen on the crash-heavy holdout.

**Funding-leg-cost note (adverse, second-order — Critic Ruling 3):** the throttle's cost lands on the
DURABLE funding leg (1.59 → 1.50 bps/cd), the OPPOSITE of A2's price-leg tax. Because the de-risked
gross collects less carry, the **IS Sharpe accretion (1.033) overstates the likely holdout benefit** —
it shades the forward expectation down, exactly where the durable core is eroded.

---

## 4. Prediction scorecard — 11/12 in-band; the one miss owned

11 of 12 predictions landed inside their bands (maxDD −23.11% ∈ [−15%,−26%]; Sharpe +1.7341 ∈
[+1.2,+1.75]; ratio 1.033 ∈ [0.72,1.04]; coverage/scalar/episode-alignment 4/4 ≥3/4; β/G1a all hit).
**The single out-of-band miss is turnover: 52.3× vs [55×, 85×]** — favorable direction. I own the
churn-model gap: I predicted the throttle's engage/release TRANSITIONS would ADD turnover over A2's
54.3×; in fact a throttled rebal trades a SMALLER notional book (gross 0.5–1.0), and the notional
reduction on ~19% of rebals OUTWEIGHS the transition churn → turnover fell. My mental model of the
churn balance was wrong; the effect is cost-favorable, but it is a genuine prediction miss, owned.

---

## 5. THE USER DECISION — recorded verbatim

> **HOLD — A3-1 is BANKED as the IS-validated family-A candidate; NO forward test yet; NO holdout
> reveal; ALL validation deferred until the family field (C/B/E2) is surveyed.**

**Operationally, this means:**
- **Family A is CLOSED for new work** — TERMINAL, n_eff 9. No A4, no re-spec, no re-gate, no further
  throttle; the shelve-on-fail budget is spent and the SUCCESS branch is likewise terminal for new
  construction work.
- **A3-1's full construction is FROZEN on the record** (the byte-frozen A2 book + the SCUD-z throttle,
  every parameter pinned in the brief + AMENDMENT 001) for a FUTURE validation decision — nothing is
  lost, nothing needs rebuilding.
- **The holdout stays SEALED.** The one-per-family-FOREVER reveal is UNSPENT. Consistent with the
  Critic's calculus (Ruling 4): spending the reveal now on a known-adverse crash-heavy window with a
  fragile boundary number is a DOMINATED move; HOLD preserves both the reveal budget and optionality,
  and (if later chosen) forward-paper-trade on genuinely-unseen post-2026-07-10 data is the charter's
  designated final arbiter with zero holdout cost and cleaner generalization evidence.
- **The reveal / forward-validation decision is REVISITED only after the other families' diagnostics/
  explorations complete** — A3-1 competes as one candidate among the eventual survivors; the reveal
  is spent, if at all, on the confirmed-best candidate with a supporting forward record, not on the
  first family to finish.

**What explicitly does NOT happen now:** no holdout spend; no forward-paper-trade launch yet; no
maxDD floor re-spec (permanently rejected); no reading of any broken-invariant robustness number; no
deployment. Any eventual deployment case is the risk-adjusted profile (Sharpe/maxDD/vol), NEVER a
buy-and-hold comparison.

---

## 6. Family-A final ledger + honest forward band

- **Family-A n_eff = 9, TERMINAL** (DIAG-A 3 cadence cells + EXPLORATION-A 3 construction cells +
  1 researcher-DOF + EXPLORATION-A2 1 + EXPLORATION-A3 1 = 3+3+1+1+1). No further inflation possible.
- **Honest forward band (carried as INFORMATION only, NOT a forecast, NOT a reveal authorization):**
  ~**+0.5 to +1.1 Sharpe, central ~0.75.** Basis: IS anchor up (A3 +1.7341 pinned / +1.7883 native)
  but offset by the +1 DOF deflation and the funding-leg erosion (§3); the throttle makes the forward
  DRAWDOWN side better-controlled (LEAD-timed squeeze de-risk) but on the crash-heavy holdout the
  drawdown is likely DEEPER than the fragile −23.11% IS number. The durable core is the funding leg
  (6/6 positive years); the price-mean-reversion leg is fragile (2022 total Sharpe −0.06). Label:
  **CHOP/MANIA funding-carry harvester, crash-break-even-neutral** (CHOP+MANIA ≈ 95% of P&L).

## 7. Track board (what's next)

Family A is BANKED and closed. The MN track continues with the remaining families:
- **NEXT: DIAG-C (OI/leverage-crowding fade)** — gated on the `fetch-oi` backfill completion.
- **THEN: DIAG-B (cointegration pairs) + DIAG-E2 (residual horizon map, 1h)** — gated on the 1h fetch.
- (DIAG-D taker-flow, DIAG-E1 residual-horizon-8h — data-ready, queued.)
The family-A reveal/forward-validation decision is revisited only after this field is surveyed.

---

## Bottom line

EXPLORATION-A3 is family A's **first and only all-HARD-pass**: the SCUD squeeze-dispersion throttle
delivered the mechanism it was designed for — fired in 4/4 drawdown episodes (2 LEAD / 2 COINCIDENT /
0 LAG), clipped the shared drawdown path 2.46pp IN PLACE, and did it **Sharpe-accretively** (1.033),
all while the beta-honesty, G3-cleanliness, and durability of the A2 book were preserved by scale-
invariance. The maxDD pass is genuine but **fragile** (+1.89pp ≈ 1.25 noise-units; misses my own
−22% robust bar by 0.89pp), and the throttle's cost falls on the durable funding leg, so the IS
accretion overstates the holdout benefit. The tier is SUCCESS in the pinned MARGINAL disposition;
A3-1 is BANKED as the IS-validated family-A candidate. **Per the USER decision: HOLD — no forward
test, no holdout reveal, all validation deferred until the C/B/E2 field is surveyed. Family A is
closed for new work (terminal, n_eff 9); the holdout stays SEALED.**

*— QR, MN track, 2026-07-10. No OOS/holdout touched; no construction changed in this document.*
