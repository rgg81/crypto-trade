# Team 08 provenance

Status: **clean-room prospective package; no result has been observed**

## Independent origin

The volatility-compression/expansion and cross-sectional-dispersion interaction was authored for
Team 08 from the public Top-40 V2 rules. It was not copied from a V1 strategy, another V2 team, a
leaderboard, a private qualifier record, or an OOS report. No other team namespace was inspected.

The mechanism began from two generic market-microstructure observations: volatility clusters, and
cross-sectional dispersion can distinguish broad price discovery from isolated dislocations. The
specific residualization, compression prerequisite, continuous expansion-versus-convergence mix,
daily portfolio rule, parameter ranges, falsifier, and risk plan in this namespace are Team 08's
prospective choices. This statement is provenance, not evidence that the thesis is profitable.

## Authorities consulted

Only the clean-room public materials authorized by the team brief were used:

- `TOURNAMENT-CHARTER-TOP40-V2.md`;
- `tournament/top40-v2/config.toml`, `README.md`, `PHASE0-POLICY.md`,
  `METHODOLOGY-DISTILLATION.md`, and `TEAM-PLAYBOOK.md`;
- public schemas in `tournament/top40-v2/templates/`;
- the public strategy and declarative-risk interfaces in
  `src/crypto_trade/tournament/protocol.py`, `_strategy_worker_v2.py`, and `risk_policy.py`; and
- the frozen Amendment 0006 decision, reviews, freezes, and integration records under
  `tournament/top40-v2/amendments/0006/`.

No snapshot rows were opened by Team 08. No development evaluator, lifecycle command, test suite,
Python process, private window, or final-OOS process was run while authoring this package.

The first executable risk state is the no-control top-level `risk_policy.json`, byte-identical to
`risk_policies/no-control.json`. Single-control and combined files are immutable source
declarations, not runtime selectors. They remain dormant unless the no-control core passes every
broad positive activation minimum; controls cannot rescue failure. Before a later policy candidate
is committed, registered, or run, the selected template must be copied byte-for-byte to root
`risk_policy.json` and every affected hash recomputed.

## Software and runtime lineage

`strategy.py` is self-contained and uses only Python's standard library plus NumPy and pandas,
which are supplied to the clean strategy worker. It performs no file, network, subprocess,
credential, repository, environment, clock, random-number, or serialized-model access. The
factory is `build_strategy()` and the only prediction method is
`target_weights(context, seed=...)`.

The passed seed is validated but is not used to randomize features, ties, or allocations. Symbols
are sorted before every cross-sectional construction, stable sorting resolves score order, and
water-filling is deterministic. The evaluator remains the sole authority for positions, fills,
fees, slippage, funding, participation, delistings, risk actions, equity, and metrics.

## Universe authority

This package is downstream of active Amendment 0006,
`top40-v2-amendment-0006-pure-crypto-universe`. The frozen canonical audit reports 667 contract
metadata symbols, 321 distinct membership symbols, and zero violations. All future registration
and result-bearing commands must use the active Amendment 0005 superset entrypoint, which delegates
ordinary commands through the exact A6 preflight. Team code does not maintain a competing stablecoin
or TradFi classifier because ticker-only inference cannot establish asset class and could diverge
from the frozen metadata authority.

## Artifact lifecycle

`families.jsonl` and `experiments.jsonl` are preserved exactly as organizer projections. The files
named `*.draft.json` or `*.template.json` are non-authoritative authoring aids. Sentinel all-zero
hashes in the trial template must be replaced by actual SHA-256 values before registration. The
family and trial timestamp placeholders must be replaced with their actual registration event
times. Creating these files does not register a family or candidate.

`frozen_config.json` freezes the team's prospective default only; it is not a tournament candidate
freeze and contains no result-derived choice. Source, configuration, risk policy, dependency,
seed, ledger, fold, neighborhood, and evidence hashes remain unresolved until the organizer
performs the lifecycle steps.

## Known limitations before evaluation

- The fixed thresholds have not been calibrated or shown profitable in IS.
- Daily rebalancing may miss short-lived releases or still incur too much turnover.
- Cross-sectional median residualization reduces, but cannot guarantee removal of, common crypto
  beta or sector clustering.
- A fixed dispersion ratio may react differently as the membership composition changes.
- Close-only realized volatility cannot identify intrabar paths, and no intrabar execution claim is
  made.
- A risk policy can reduce exposure but cannot manufacture alpha; every control must survive its
  preregistered ablation and doubled-cost rerun.
