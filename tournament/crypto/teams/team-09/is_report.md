# team-09 IS report — t09-trade-size-composition-v3
## Strategy: trade-size composition cross-section (W=42, B=90, centered rank, no smoothing)

All headline numbers in Section 1 come from `out/is_metrics.json` (team-run, schema 1,
window 2020-01-01 → 2024-07-01 exclusive). Research-context numbers in Sections 2-5 are
scratch-evaluator results, cited by their evaluator-stamped ledger ids (experiments.jsonl,
10 entries, logged before results were read; scratch code under `out/scratch/`).

## 1. Headline results (team-run artifact)

| Metric | 1x | 2x-stress |
|---|---|---|
| Net IS Sharpe (monthly, √12) | **+0.8299** | **+0.5900** |
| Max drawdown | −0.4393 | −0.4532 |
| Total return | +1.9600 | +1.0039 |
| Ann. turnover | 80.72 | 80.72 |
| Median names long / short | 19 / 19 | 19 / 19 |
| Months | 54 | 54 |
| Regime Sharpe bull / bear / chop | +1.2065 / +1.0532 / **−0.2849** | +1.0104 / +0.8215 / −0.5818 |
| Total funding P&L (raw frac) | **+0.1147** | +0.1147 |
| Total cost (raw frac) | 0.2305 | 0.4610 |
| Mean gross / mean net | 1.0000 / ~0 | 1.0000 / ~0 |

Signal: long rising average-trade-size names (large-trade flow), short shrinking-ATS /
exploding-count names (retail swarm), from `quote_volume` and `trades` only — no price,
OI, funding, or ratio inputs; no randomness. Breadth floor passed (19/19 ≥ 5). Harness:
all six checks PASS; team tests 7 passed.

## 2. Mechanism verification (ledger e05-e08)

- **F3 load-bearing (the registered check): PASS decisively.** Identical pipeline with
  the composition term replaced by attention-fade controls: volume-spike fade **−0.58**,
  trade-count-spike fade **−0.30**, vs the composition book **+0.83** (e08, W=42 cells).
  Both controls are outright money-losers on this substrate — **the trade-size
  composition term IS the edge**, not attention/volume per se.
- **Funding sub-hypothesis CONFIRMED**: total funding P&L +0.1147 (team-run). Leg split
  (e08): the swarm-short leg COLLECTS funding (+0.14 raw; crowded-long names pay positive
  rates), the whale-long leg pays a little (−0.09). Funding-off sensitivity (e10): Sharpe
  +0.70 → funding contributes ≈ +0.13 Sharpe — a real tailwind, not the whole edge.
- Grid structure (e06/e07): the h=1 row is a genuine W-plateau (+0.83…+0.98 across
  W=5-42 @1x); Sharpe decays monotonically in extra smoothing h. 2x-stress ordering
  inverts (W=42 best at +0.59) — the shipped cell is the stress-robust end of the plateau.

## 3. Momentum-overlap disclosure (ledger e05, e08-e10; orchestrator escalation ruling: SHIP with full disclosure)

Discovered in e05 (xsec Spearman comp↔ret21 = +0.35) and pursued with ex-ante-logged
decision bars (e09):

- A ret21 price-momentum reference book (a CLAIMED family — measured strictly as a
  diagnostic, never shippable by team-09) scores +1.28, with **+0.46 monthly correlation**
  to our candidate (+0.69 for the faster W=9 variant).
- Momentum-residualized composition book: **net −0.03** (residualization doubles turnover,
  165 vs 81/yr, and costs erase it) but **+0.50 pre-cost** (**+0.38** with funding also
  off; bull +0.71 / bear +0.81) — the registered mechanism carries REAL momentum-orthogonal
  gross alpha; in net terms the shipped slow design's edge is substantially carried by the
  momentum-correlated component.
- The e09 ex-ante bar ("net residual ≤ 0 ⇒ escalate") FIRED; the orchestrator ruled
  **SHIP with full disclosure** (this section). The strategy implements the registry text
  literally, with zero price inputs; the overlap is an economic property of the substrate
  (large-trade flow rides winners; swarms pile into laggards), not a design choice.

## 4. Honest weaknesses & audit trail

- **Chop is negative: −0.2849 @1x (−0.5818 @2x).** Leg decomposition (e08) locates it:
  the whale-long leg bleeds in dead markets (FTX-aftermath 2023, post-halving 2024
  windows), while the swarm-short leg is mildly positive there. Pre-registration
  predicted chop > bear ≈ 0; realized is bull ≈ bear > 0 > chop. Deviation disclosed.
- **Robustness sensitivity (e09)**: B=180 → +0.54; z-transform → +0.60; vs +0.83 for the
  pre-registered defaults (B=90, rank). Knob sensitivity 0.23-0.29; defaults were fixed
  in the brief BEFORE the grid ran and variants are worse, so defaults stand — but the
  selected cell sits toward the favorable side of its robustness band.
- **Selection amendment audit trail**: strict plateau rule 1 picks (W=9, h=1) (+0.98).
  The amendment to (W=42, h=1) — max 2x-stress, least-bad worst-regime, lowest turnover,
  horizon fidelity to the registry text — was written into the ledgered e09 entry BEFORE
  e09/e10 were run. (9,1) numbers remain on record in the brief for the Critic.
- Early-2020 rows can be flat (MIN_NAMES=10 guard against the 3-18-name universe).

## 5. Dead-family record (mandatory; ledger e01-e04, brief Appendix A)

team-09's originally approved family **t09-liq-squeeze-reversal-v2** (post-liquidation
snap-back) was FALSIFIED before this strategy existed: all 9 pre-registered book cells
−2.31 to −3.18 @1x (e02); center cell −1.31 pre-cost/pre-funding (e03); event-conditional
forward returns wrong-signed at every threshold and 1-9-candle horizon and — the killing
result — **monotonically worse with stronger cascade evidence** (−182 bps t=−3.3 →
−689 bps t=−2.7 as thresholds tighten), in bull, bear, and chop alike (e03); OI-collapse
confirmation neutralizes the continuation but never yields a harvestable bounce (best
+6.6 bps, t=0.6, below round-trip cost; e04). At 8h granularity the snap-back is absorbed
intra-candle; what remains is continuation. The sign-flip was NOT shipped (it belongs to
claimed continuation families); the pivot to this family was orchestrator-approved and
FCFS-resolved. Scratch provenance: `out/scratch/sig.py`, `e01_coverage.py`, `e02_grid.py`,
`e03_eventstudy.py`, `e04_oi_eventstudy.py`.

## 6. Honest expectations

This book is a bull/bear performer with a disclosed chop bleed and a disclosed momentum
overlap: if cross-sectional momentum decays in the holdout, the net edge here decays with
it (correlated failure mode with the price-persistence families), cushioned by ≈ +0.13
Sharpe of structural funding tailwind and by whatever the momentum-orthogonal composition
alpha (+0.50 pre-cost) contributes at the shipped low turnover. The +0.83 IS Sharpe sits
about 1.5 noise-floor units from zero on 54 monthly points; the honest holdout
expectation is positive-but-lower, with the 24-month noise floor making any single-window
verdict weak. We ship it as a mechanism we verified (F3 controls decisively negative,
funding legs as registered), whose weaknesses we have measured and stated, rather than as
a claim of discovered certainty.
