# EXPLORATION-011 & 012 — improving the iter-010 baseline (turnover, bad months, ensemble)

**Track:** metals portfolio. **Date:** 2026-06-26. **User mandate:** "push more... invest in dropping
transaction costs (fewer trades), study the bad months, maybe an ensemble of models — but NO CHEATING,
look-ahead bias NOT allowed; no pressure, this one is good already." All leak-free, IS-only, position-level
honest accounting, Critic leak-checked.

## iter-011 — hysteresis DEADBAND (user priority #1: fewer trades)
The position-level accounting exposed turnover as a material cost (~1.4%/yr). A hysteresis deadband
re-trades a metal only when its target moves >δ from the held position (proven crypto iter-020 trick;
strictly causal). δ=0.02: turnover −19%, cost 1.49→1.20%/yr, and the saving LIFTS the Sharpe — IS
+0.16→+0.21, BULL +1.60→+1.66, BEAR preserved +0.36. Leak-free (future-corruption 0.0), reconcile bit-exact.

## Bad-month diagnostic (user priority #2)
The 10 worst IS months are dominated by the **long-gold anchor whipsawing**; the losing regime is the
**transitional chop (breadth 0.3-0.5): mean −0.40%/mo, 48% win**. Mitigations TRIED + FAILED (recorded
near-dead-ends): anchor-taper on breadth LEVEL crushes the bull (level can't separate bull-pullback from
bear-onset); uniform anchor-de-risk WASHES OUT via gross-norm (the structural law). The chop loss is the
irreducible cost of the anchor's long-bias — not fixable from within the anchor.

## iter-012 — COT positioning ENSEMBLE (user priority #3 — the flagship)
The bad-month fix had to come from OUTSIDE the price sleeves. Ensemble a small dose of the iter-004 CFTC
managed-money CONTRARIAN positioning tilt (GOLD/SILVER only — uncorrelated, NON-PRICE, leak-safe). It fades
crowd extremes independent of the price whipsaw → the chop bad-bucket is NEUTRALIZED (−0.38%→−0.04%/mo) and
every regime lifts: **IS +0.21→+0.38, BEAR +0.36→+0.58, BULL +1.66→+1.72, worst-DD −13.6%→−12.5%.** cot_w
is a smooth IS-basin PEAKING at 0.3. A 9-member lookback ensemble (also tried) diluted the bull — rejected.

## Scorecard (leak-free, position-level honest, canonical data)
| book | BEAR | IS | BULL | worst-DD |
|---|---|---|---|---|
| iter-010 ACCEL gate | +0.36 | +0.16 | +1.60 | −13.6% |
| iter-011 + deadband | +0.36 | +0.21 | +1.66 | −13.6% |
| **iter-012 + COT (BASELINE)** | **+0.58** | **+0.38** | **+1.72** | **−12.5%** |

## Critic (2 rounds) → iter-012 PROMOTE-WITH-CAVEAT
**COT release-timing leak GENUINELY CLOSED** (the user's hard constraint): +6d lag conservatively correct,
grid-restricted under truncation, peek-earlier falsifier holds, 2 committed alignment tests + reconcile
bit-exact WITH the COT. Gold/silver-only correctly avoids the OOS-falsified full-4 (chose OOS-robustness
over the higher full-4 IS — anti-snoop). Blockers cleared: BASELINE rewritten to the chain; 2008 script
repointed; `iter_012_robustness.py` commits the cot_w/δ/w_blend IS basins; CI peek-earlier + COT-in-desk
leak tests; live COT refresh + cache-clear wired (`live_metals._refresh_cot` → `ingest_cot.refresh_recent`).
Caveats: thin IS with 5+ knobs (selection haircut — treat as diversification + chop-repair, not a Sharpe
level); +6d holiday-week marginality (consider +7d); bear N≈42 not individually significant.

## Honest takeaway
The campaign turned a +0.16-IS / +0.36-BEAR book into a **+0.38-IS / +0.58-BEAR** one — leak-free, lower-
turnover, bad-months-repaired — by cutting cost (deadband) and ensembling an uncorrelated non-price sleeve
(COT). The IS is still thin (treat as diversification), but the chop-repair + the all-weather profile are
mechanism-grounded and Critic-cleared. Files: iter_011_deadband.py, iter_012_cot_ensemble.py,
iter_012_robustness.py, tests + the live COT refresh. DEPLOYED PAPER, not real capital.
