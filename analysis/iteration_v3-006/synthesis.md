# iter-v3/006 — Seed Derivation Demo Synthesis

Producer-side validation that `_derive_ensemble_seeds(outer_seed)`
(committed at SHA `9314db4`) replaces the pre-fix hardcoded
`ENSEMBLE_SEEDS = [42, 123, 456, 789, 1001]` with a per-outer-seed
deterministic distinct 5-seed list. The 6 adversarial tests in
`tests/strategies/ml/test_outer_seed_propagation.py` already pass at
SHA `9314db4`. This script complements those tests with the
human-readable artifacts: `derived_ensembles.csv`, `overlap_matrix.csv`,
and `legacy_check.csv`.

For the 5 representative demo outer seeds `[42, 17, 100, 999, 8675309]`:

- outer=42: inner=[191664963, 1662057957, 1405681631, 942484272, 929893137]
- outer=17: inner=[1591207480, 1814784297, 230512677, 345687080, 983484580]
- outer=100: inner=[1646872011, 1793109396, 266670593, 1281090017, 172364403]
- outer=999: inner=[1747827325, 1672513988, 374097583, 369901117, 388482298]
- outer=8675309: inner=[1574131626, 813751500, 727432243, 1749148543, 778347199]

Pairwise off-diagonal Hamming-distance overlap is **10/10
pairs with zero shared inner seeds** (max overlap across pairs:
0). None of the 5 demo seeds
reproduces `LEGACY_ENSEMBLE_SEEDS=[42, 123, 456, 789, 1001]`
(0/5 reproductions;
0 total inner seeds
shared across all demos). The fix produces structurally distinct inner
ensembles per outer seed, satisfying the prerequisite for any meaningful
multi-seed Pareto validation. iter-v3/006's central test (Phase 6,
`--seeds 2 --n-trials 10` on BCH-only) verifies the consumer-side
property that distinct ensembles produce distinct trade distributions
(per-seed Sharpe std > 0); this demo only verifies the producer-side
algebra.
