# REVIEW-A — Critic Adversarial Review of EXPLORATION-A Results (MN track, funding-carry)

**Reviewer:** Quant Critic (Fable, read-only). **Date:** 2026-07-10. **Persisted by orchestrator.**
**Contract:** briefs-portfolio-mn/EXPLORATION-A.md + PRE-RUN AMENDMENT 001. Quarantines honored;
holdout SEALED and unspent throughout.

## VERDICT (frozen §5 map): **FAIL — "other neutrality HARD" (G3).** Not revealed; no automatic
A2 (A2 was G2-CRASH-scoped). The G3 gate is SPENT for Cell 1 on the IS window; the adjudication
below does not overturn the tier.

## Gate scorecard (independent): 10/11 HARD pass
G1a 96.0%/max 0.1769 PASS (thin: +1.0pp / 0.023); G1b 100%/0.1016 PASS; **G2-CRASH β +0.0103
PASS decisive** (unhedged already +0.0178 — DIAG-A's +0.172 did not translate to the engine
book); G2-MANIA −0.0113 PASS; **G3 max|Σw|/gross 0.2365 vs 0.10 FAIL (5.9% of rebals breach)**;
G4 worst=CRASH t +0.26 PASS (ex-burned-window t≈0 — see attribution); G5 SOFT-fail (CHOP 69.6%);
performance HARD all pass (Sharpe +1.7753; 2×-GT +1.5616 = 0.88×; maxDD −24.68% — 0.32pp margin;
turnover 54.9×; G-durable 6/6 yrs; G-sample OK; G-contam 1.20× stronger ex-window).

## Central adjudication — the G3 breach is BOTH, weighted toward mis-specification
- Mechanism: the alpha book is dollar-neutral EXACTLY (Σw_alpha ≡ 0 at every breach) but carries
  negative BTC beta (to ~−0.22 in 2024-25; long low-beta negative-funding majors vs short
  high-beta memes). Cancelling it requires a LONG BTC hedge leg = the dollar-net. A spot-leg
  beta hedge mathematically cannot satisfy |Σw|≤0.10·gross when |β_alpha|>0.10. The brief's §1.7
  "hedge net small" premise was unexamined; the G3 band [0.02,0.12] rested on it (the Critic
  co-owns that band from pre-flight — the /007 rho_bar error class: regime-tail exposure
  mis-modeled from a full-sample point).
- (i) Mis-specification vs the charter's own doctrine (dominant): the charter mandates
  REALIZED-BETA neutrality, explicitly not dollar-neutrality; G2-CRASH +0.0103 shows the 0.22
  dollar-net did NOT translate into realized directional risk. Gate indicted à la /007 G-crash.
- (ii) But the residual risk content is genuine: G1/G2 are windowed averages — they do not bound
  the single-candle gap scenario under beta-estimation error; the +0.22 leg carries real
  margin/financing/liquidation footprint. The PLAN chose the overlay OVER cross-sectional
  neutralization, and this net exposure is that choice's direct consequence.
- Treatment: tier stands. The family cannot go to holdout until the neutrality specification
  separates (a) realized-beta doctrine [passing] from (b) a principle-anchored hedge-notional
  bound [the genuine residual], or the design meets the frozen gate outright.

## Admissible follow-up (/007 precedent applied)
(a) NO IS re-gate of Cell 1 — outcome known, FORBIDDEN. (b) A doctrine-motivated gate
re-specification is ADMISSIBLE only as a dated PLAN-AMENDMENT, +1 n_eff, number NOT fitted to
0.2365, denominator pinned, scored only on unseen data, contamination disclosed — SECONDARY
path. (c) **PREFERRED: a NEW construction with unseen G3 numbers — cross-sectional
beta-neutralization of the alt weights (the PLAN §4.1-rejected alternative) or overlay + a
dollar-net cap on the alpha book — a legitimate EXPLORATION testing the sharper question: can
this carry edge be neutralized WITHOUT ~22% directional BTC exposure?**

## Honest attribution (contamination-twin split)
Crash-bucket β is clean; crash-bucket PROFIT is a burned-window artifact (+0.54 bps/cd full →
−0.01 ex-window). The book is **crash-NEUTRAL, not crash-profitable**; 98% of P&L is CHOP+MANIA.
"Carry pays in ALL regimes" downgrades to "pays in CHOP/MANIA; break-even-neutral in CRASH."
Directly adverse note: the sealed holdout (2026+) is crash-heavy — the earning buckets are
exactly what it starves.

## Prediction scoring + technical record
Edge predictions conservative (Sharpe/2×/mania above band — honest direction). Mechanistic
misses: turnover 2× low (rank-weight dynamics ≠ decile swaps; G-turnover was a dead gate);
cap-bind 0% at N40 (the Critic's own C2 min_members rule excludes the binding region — cap
redundant at N40, binds only N20 22.3%); ETH-arm 2% vs [5,50] (BTC leg alone neutralizes ETH);
G3 0.2365 vs [0.02,0.12] — the consequential miss, co-owned. **Second analytic-2× invalidation
channel (NEW RULE for the catalog):** any stateful control reading realized cost-bearing returns
(hedge arming, dd-brake, vol-target) can flip DECISIONS under a cost change → analytic cost
twins are valid ONLY for stateless constructions; ground-truth re-runs mandatory otherwise
(pre-flight C1 saved this run; drift 2.4e-3 on arm-flip cells vs 2.6e-4 pure). G-durable's +16
"Sharpe" is an income-drip artifact — a sign/consistency check only, NEVER a forecast anchor.
Thin margins flagged: G1a +1.0pp, maxDD 0.32pp (unhedged cell already −26.28% — the hedge pulls
it inside by a hair); do not expect them to hold OOS.

## Integrity — all PASS
Warmup 273/293 asserted; identical mask all cells/tiers; bit-identical re-run; leg recon
1.11e-16; hedge-inert control 0.0; holdout guard on all 22 grids; engine-extension tests
non-vacuous (multi-pass fixed point proven necessary; skip-rebal counter validated; hedge-sized-
on-capped-book ordering). 86/86 tests.

## Ledger + honest forward band
Family A ≈ 7 DOF (+1 if the gate re-spec path is taken). IF a frozen-gate-passing version ever
reaches the holdout: **honest band ~+0.5 to +1.1, central ~+0.75–0.80** (funding leg = durable
core 6/6 yrs; price-MR leg fragile — 2022 −0.165; phase-luck already removed by construction;
crash-heavy holdout is the adverse regime for a CHOP/MANIA earner). Holdout spend requires a
correctly-specified neutrality PASS first.

## Path forward (family alive)
1. **Cross-sectional beta-neutralization construction (PREFERRED — unseen G3 numbers, frozen
   gate untouched).** 2. Doctrine-motivated G3 re-specification (PLAN-AMENDMENT, +1 n_eff,
   unseen-data scoring only). 3. Re-scope the mechanism claim as a chop/mania harvester with
   explicit crash-break-even disclosure (+ optional dispersion-conditional crash de-risk).
