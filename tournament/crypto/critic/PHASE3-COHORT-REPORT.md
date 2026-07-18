# crypto-cup-01 — Critic Phase-3 Cohort Report

**VERDICTS: 10/10 PASS. Zero BLOCK-PENDING-FIX. Zero FAIL. Zero integrity DQs.**

Audit basis: per-team harness reruns byte-diffed against frozen `out/harness.json`; independent
greps (incl. `out/scratch/` and non-.py files); SHAs recomputed; ledgers/briefs/reports/
provenance read; team test suites executed; every journaled amendment, pivot, and ruling
verified against primary artifacts. No holdout data, `results/`, or the holdout env touched.

## Cross-team plagiarism & mechanism-drift check (all ten trees)

- **No code or idea plagiarism found.** Ten distinct constructions on ten registry-distinct
  families; shared idioms (eligibility reindex-fillna(False), centered ranks, EWM smoothing)
  are interface/menu-generic with independent structure, constants, and commentary in every
  tree. Cross-team textual references are registry-based boundary prose (the registry is
  team-readable); none read another team's tree. Several teams' UNUSED backup registrations
  name families other teams later claimed — independent convergence at idea-menu level,
  supporting the non-plagiarism reading.
- **Construction-level drift comparison (t08 vs t10 vs t03/t04/t02):** all five load on price
  persistence in outcome; constructions are genuinely distinct: t03 = XS rank of
  market-residual return t-stats; t04 = per-name multi-horizon log-price t-stats, no XS
  operation; t02 = range-relative Donchian channel position; t08 = σ-scaled displacement rank
  with a hard binary sign(ΔlogOI) gate (positioning-ledger input); t10 = return rank with a
  continuous [0,1] volume-participation gate (traded-volume input). Different inputs, gate
  algebra, and horizons; the two gated books are the closest conceptual pair but were
  separately registry-vetted and share no construction. No family-misrepresentation anywhere.

## Cohort note for Stage-1 readers

1. **The field is momentum-correlated.** Six of ten books load on price persistence — t02,
   t03, t04, t08, t10 by construction; t09 by measured correlation (+0.46 monthly vs a
   momentum reference). Mechanisms are distinct (diversity rule satisfied), but the failure
   mode is shared: a chop-dominated holdout hits most of the board simultaneously. The
   genuinely decorrelated books are t01 (funding carry), t05 (taker flow), t06 (positioning
   contrarian), t07 (vol dynamics).
2. **Universal front-loaded edge.** Every team that measured split halves reports 2020-21
   dominance: t01 3.49/1.44, t02 3.17/1.14, t04 2.64/0.77, t05 2.29/0.72, t07 1.22/0.80, and
   t10's worst quarter is the final IS quarter. All ten independently state forward run-rates
   well below their headline. Stage-1 ranks the 54-month number; rank gaps partly measure
   2020-21 exposure, not durable edge.
3. **Noise floor.** At Sharpe ≈ 1–2 over 54 monthly points the SE is roughly ±0.4. The
   t04/t05/t10 cluster (1.609/1.501/1.419) and the t06/t07 pair (1.176/1.025) are statistical
   ties; the locked rule still decides, but readers should not over-read those orderings.
4. **Two boards carry structural coverage dilution.** t06 (~21 live months of 54; run-rate
   ≈ 1.60 vs board 1.18) and t08 (~30 active months; run-rate ≈ 0.94 vs board 0.46) are ranked
   on diluted numbers — charter-consistent under the locked rule, and both teams disclosed the
   decomposition; their holdout windows have full coverage from candle one, so their board
   numbers understate their forward priors relative to other teams'.
5. **Two books run persistent net-long tilts near the 0.25 cap** (t08 +0.163, t10 +0.212, vs
   ~0 for the rest). Engine-legal and visible in mean_net, but a holdout bear treats them
   differently than the zero-net books.
6. **Selection-on-IS discipline was generally strong**: pre-registered plateau/tie-break rules
   throughout; three teams demonstrably left higher-scoring configs on the table (t03, t06,
   t10); amendments were pre-logged (t09); grid extensions were pre-committed and terminated
   (t07). Residual researcher degrees of freedom are nonzero everywhere (two consumed
   sign-branch changes: t07's H2, t10's fade-death) — all ledgered and bar-raised, none hidden.
7. **Process hygiene note for the orchestrator**: one cross-team aggregate fact ("lowest
   turnover in the field") was conveyed to team-07 pre-freeze and is quoted in their
   is_report. It arrived post-selection and is harmless here, but the zero-cross-team-
   information principle is cleanest if even aggregates wait until all freezes are complete.
