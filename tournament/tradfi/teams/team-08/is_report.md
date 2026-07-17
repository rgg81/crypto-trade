# team-08 — IS Report: NEGATIVE RESULT (family falsified, no submission)

Family: `t08-short-horizon-reversal-v1` — plain own-name 1-5d cross-sectional reversal.
Verdict: **pre-registered falsifier FIRED across the entire design space. No strategy.py, no
freeze, no `out/is_metrics.json`.** This report documents the negative result with the same
precision a positive one would get (charter §8).

Number provenance: every raw metric below is the output of the evaluator
(`tournament.engine.run_is` / `evaluate`), dumped verbatim to `out/exp0NN_*.json` by
`out/scratch/scratch_reversal.py`. The only derived column is `gross_est` = 2·S1x − S2x
(linear cost extrapolation from the evaluator's own two cost tiers), labeled as such.

Panel: 65 names, 3,646 US trading days, 2010-01-04 → 2024-06-28; median valid names/year
42 → 65. All books shown satisfy the breadth floor (median names/side ≥ 5; full-rank books
run 24-25/side, the most concentrated q=0.15 book runs 8/7).

## exp-003 — lookback grid (rank weights, FULL, no smoothing)

| k | S@1x | S@2x | gross_est | maxDD@1x | ann. turnover |
|---|------|------|-----------|----------|---------------|
| 1 | −1.819 | −3.963 | +0.325 | −0.989 | 331.9 |
| 2 | −1.468 | −3.094 | +0.158 | −0.973 | 229.8 |
| 3 | −1.148 | −2.565 | +0.269 | −0.931 | 187.0 |
| 4 | −1.115 | −2.388 | +0.158 | −0.924 | 161.4 |
| 5 | −0.742 | −1.833 | +0.349 | −0.867 | 143.8 |

## exp-004 — weighting (k=5): rank −0.742 / z −0.967 / zwinsor −1.007 @1x. Rank dominates gross and net.

## exp-005 — EWMA smoothing (k=5, rank, FULL)

| halflife | S@1x | S@2x | gross_est | turnover |
|---|------|------|-----------|----------|
| 0 | −0.742 | −1.833 | +0.349 | 143.8 |
| 1 | −0.524 | −1.297 | +0.249 | 103.1 |
| 2 | −0.484 | −1.121 | +0.153 | 84.4 |
| 3 | −0.472 | −1.032 | +0.088 | 73.7 |
| 5 | −0.470 | −0.935 | −0.005 | 60.9 |
| 8 | −0.464 | −0.846 | −0.082 | 50.1 |

Finding: the alpha decays under smoothing exactly as fast as the cost drag — net is pinned
at ≈ −0.47 and the gross itself is gone by h=5. The edge lives only in signal freshness.

## exp-006 — last-day handling (k=5, rank, h=0): FULL −0.676-adjacent best is INTRA

FULL −0.742 (gross_est +0.349) / LAG1 −0.816 (+0.275) / INTRA −0.676 (+0.463) @1x.
Finding: dropping the uncapturable overnight leg (INTRA) gives the best harvestable gross —
the overnight gap's reversion completes before the open[t+1] fill, as feared in the brief.

## exp-007 — tail concentration (k=5, rank, INTRA, h=0)

q=0.5: −0.676 (gross_est +0.463) / q=0.35: −0.624 (+0.490) / q=0.25: −0.650 (+0.374) /
q=0.15: −0.639 (+0.251) @1x; turnover RISES 150→196.
Finding: no alpha density in the tails — extreme ranks revert less (informational moves).

## exp-008 — extreme-move gate (k=5, rank, INTRA): z_max inf −0.676 / 4.0 −0.679 / 3.0 −0.715 / 2.5 −0.756 @1x. Dead axis.

## exp-009 — joint k × halflife cross (rank, INTRA)

| k | h | S@1x | S@2x | turnover | sub-2010-16 | sub-2017-24 |
|---|---|------|------|----------|-------------|-------------|
| 1 | 2 | −0.614 | −1.962 | 201.7 | −0.809 | −0.412 |
| 1 | 3 | −0.461 | −1.619 | 170.3 | −0.623 | −0.289 |
| 1 | 5 | −0.315 | −1.255 | 134.4 | −0.499 | −0.117 |
| 3 | 2 | −0.458 | −1.336 | 121.4 | −0.429 | −0.482 |
| 3 | 3 | −0.417 | −1.181 | 104.5 | −0.355 | −0.470 |
| 3 | 5 | −0.408 | −1.042 | 84.6  | −0.352 | −0.458 |
| 5 | 2 | −0.442 | −1.104 | 87.6  | −0.380 | −0.497 |
| 5 | 3 | −0.439 | −1.023 | 76.3  | −0.370 | −0.502 |
| 5 | 5 | −0.449 | −0.933 | 62.8  | −0.449 | −0.462 |

## exp-010 — halflife boundary closure (k=1, rank, INTRA)

| h | S@1x | S@2x | turnover | sub-2010-16 | sub-2017-24 |
|---|------|------|----------|-------------|-------------|
| 8  | −0.224 | −0.987 | 106.5 | −0.491 | +0.064 |
| 12 | −0.188 | −0.825 | 86.4  | −0.543 | +0.198 |
| 20 | −0.154 | −0.657 | 65.8  | −0.606 | +0.324 |
| 30 | −0.124 | −0.532 | 52.8  | −0.629 | +0.380 |

Boundary finding, honestly bounded: whole-window net stays negative through h=30, and at
h ≥ 8 the construction leaves the registered family (EWMA h=30 over 1-day intraday ranks ≈
43-day effective lookback = a medium-horizon intraday-component fade, adjacent to team-07's
approved overnight-vs-intraday family). The late-window sub-period positives up to +0.38
belong to that out-of-family mechanism and are NOT claimed as evidence for this family.

## Regime profile (representative configs, @1x)

| config | bull | bear | chop | overall |
|---|------|------|------|---------|
| k=5 rank FULL h=8 | −0.66 | +0.47 | −0.22 | −0.464 |
| k=1 rank INTRA h=5 | −0.48 | +0.58 | −0.36 | −0.315 |
| k=1 rank INTRA h=30 | −0.27 | +0.59 | −0.03 | −0.124 |

The bear-positive / bull-negative shape is the textbook liquidity-provision signature: the
mechanism exists on this panel; it is simply smaller than 6 bps/side everywhere it is fresh
enough to matter.

## Falsifier disposition

Pre-registered (registration + brief §6): killed if net Sharpe@1x ≤ 0 across the entire
(k, weighting, variant, h, q, z_max) space. Result: 31/31 evaluated configurations negative
at 1x AND at 2x; the pre-registered selection rule's feasibility filter (§5.1, Sharpe@2x > 0)
admits the empty set; the modern-era clause never becomes reachable in-family. FALSIFIED.

Ledger: 8 material experiments (exp-003..exp-010) + 2 registration lines; 40-line hard cap
untouched. A DNF is the honest outcome for this family on this panel at these costs.
