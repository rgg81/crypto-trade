# Team 06 handoff

Status: coherent base package ready for organizer review; **not registered, not run, not qualified**.
There are no performance results or claims.

## Frozen base

- Family: `t06-balanced-trend-reversal-v1`
- Candidate: `t06-balanced-trend-reversal-v1-base`
- Entrypoint: `strategy.py:build_strategy`
- Seed: `20260801`
- Requested exposure: gross <= 0.48, absolute net <= 0.04, symbol <= 0.07
- Policy: `risk_policy.json` (volatility target + drawdown brakes + turnover cap)
- Evidence: six chronological fresh-instance folds declared in `folds/`
- Candidate rule: base only; a neighbor can never replace it

## Organizer checklist

1. Review the strategy/config/lineage/risk bytes and the hard-gate/falsifier language. Resolve any
   source/config inconsistency before registration; afterward, change only through the formal
   amendment or new-family path.
2. Copy `family_registration.template.json`, replace only its organizer timestamp sentinel,
   validate against the public family schema, and register through the lifecycle. Do not hand-edit
   `families.jsonl`.
3. Build the exact base source bundle, compute SHA-256 values, copy and complete
   `trial_registration.template.json`, validate it, and register the base before any result is
   read. Do not hand-edit `experiments.jsonl`.
4. Run only the visible-development base. Populate the six model-artifact hashes and stitched
   return hash in a copy of `walk_forward_manifest.template.json`; preserve centrally generated
   complete evidence and resource accounting.
5. Apply every base-core gate in `research_brief.md` noncompensatorily. On any failure, leave all
   neighbors and ablations dormant, record the negative result, and make a documented pivot-or-DNF
   decision within the cumulative budget.
6. Only after base-core pass, register all four neighbor trials before reading any neighbor result.
   Build each from its byte-distinct JSON/wrapper in `neighbors/`, keeping every undeclared
   parameter identical to base. Run them as one batch and fill a copy of
   `parameter_neighborhood_manifest.template.json` with real artifact hashes. Require >= 3/4
   profitable and median Sharpe >= 0.50; retain the base regardless of neighbor ranking.
7. Only after neighborhood pass, register/run the four dormant attribution policies in
   `risk_policies/`; the combined policy result already belongs to base. Produce base/doubled-cost
   readouts for no-control, each control, and combined. Never switch policies from those results.
8. Run the organizer integration cases in `synthetic_test_plan.md`, including next-open execution,
   funding order/sign, costs, sleeve reconciliation, risk ordering, reentry prevention, and two
   clean-process reproductions.
9. Freeze only if the base passes every development and attribution requirement and all hashes and
   provenance agree. Consume the one-shot private ticket only after the complete freeze. Private
   failure is terminal DNF; no numerical private feedback may be exposed.

## Template warning

Files ending in `.template.json` intentionally contain angle-bracket sentinels and therefore are
not schema-valid final artifacts. They prevent invented hashes/timestamps. Populate and validate
copies from organizer-owned facts; never replace a sentinel with zeros or a guessed value.

## Scope ledger

Planned maximum material configurations are nine: one base, four conditional neighbors, and four
conditional risk ablations. No mechanism pivot, private ticket, final-OOS view, or measured trial
has been consumed by this design-only handoff. The organizer journal, not this statement, becomes
authoritative once work begins.
