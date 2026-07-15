# Pivot 1 provenance: Directional Auction Absorption

## Formation scope

DAA was formed on 2026-07-15 as a pre-data first pivot after the preregistered C3RP stop rule fired.
The stop decision used only team-02's own experiment ledger and canonical runner summaries. No
underlying return, trade, event, position, or target series was opened for pivot design. No market
snapshot, another V2 team, V1 mechanism/result, private/final observation, leaderboard, ballot, or
historical portfolio research was accessed.

No pivot registration, trial registration, evaluator, lifecycle command, strategy/config/risk
edit, or commit was performed while creating this package.

## Independent origin

The mechanism follows generic auction reasoning rather than the failed family's parameters:

1. per-symbol path efficiency measures whether an auction moves directionally with limited
   backtracking;
2. normalized taker-buy share measures aggressive order direction;
3. closing location measures the bar's realized price response;
4. their gap identifies latent demand/supply absorption;
5. a fixed cross-sectional blend selects relative leaders and laggards with equal side budgets.

No C3RP date, symbol, coefficient, position, trade, target, or return path informed DAA. The only
C3RP information used beyond family identity was the published team-02 terminal/summary evidence
needed to enforce the stop: baseline insolvency and the no-direction diagnostic's negative
aggregate, doubled-cost, drawdown, bull, and bear metrics.

## Distinctness record

DAA excludes every defining C3RP transform:

- no common cross-sectional median market return;
- no beta or residual return;
- no slow/fast residual trend and residual reversal blend;
- no persistence/breadth state or sigmoid;
- no realized funding feature;
- no market-direction side tilt;
- no inverse-volatility name weighting.

DAA instead uses OHLC closing location and taker-buy quote-volume share, fields absent from C3RP's
mechanism, joined to a fixed per-symbol path-efficiency score. Diagnostic removals cannot be
deployed, preventing a cosmetic collapse into plain momentum.

## Frozen reproducibility commitments

- Family: `team-02-directional-auction-absorption-v1`.
- Parent: `team-02-causal-crowding-residual-persistence-v1`.
- Reference: `team-02-daa-reference-001`.
- Runtime seed: `20260801`; team search/test namespace: `2026080102`.
- Feature cutoff: one full 8-hour bar (`t-8h`).
- Arithmetic: finite binary64, natural log, deterministic `fsum` semantics, `epsilon=tau=1e-12`.
- Reference signal: 12-day path efficiency plus three-bar half-life-two absorption gap at fixed
  60/40 rank weights.
- Reference portfolio: exact quarter selection, minimum six per side, equal `0.40/0.40` requested
  budgets, gross `0.80`, cap `0.06`, daily rebalance, no control.
- Six contiguous folds cover all visible development; selection embargo is 30 calendar days.
- Every material and diagnostic arm counts before execution.
- No-control reference failure stops DAA before any risk study.

## Budget provenance

Team-02 consumed two C3RP material configurations. DAA reserves at most 37 of the 78 remaining:
one reference, five diagnostics, eleven additional coarse cells, four portfolio/schedule cells,
eight neighbors, and eight risk/cost observations. At least 41 configurations remain unallocated.
Formal pivot count remains zero until the organizer accepts `family-registration.json`; it would
then become one.

## Mechanism fingerprint

The proposed mechanism fingerprint is the SHA-256 digest of the exact validated bytes of
`pivot-01/family-registration.json`:

`416f4a58454efe980f600f58a5590f2a9eeebaaf04994fe1cff4e5d124f1e26e`

The existing `families.jsonl`, `experiments.jsonl`, current strategy, frozen config, and risk policy
are not edited by this proposal.
