# team-02 formation provenance

## Scope and origin

This initial-family specification was independently formed in the team-02 clean room on
2026-07-15. It is a causal hypothesis and preregistered research plan, not a conclusion from
market results. No V1 strategy, team, result, report, ballot, leaderboard, historical portfolio
research, other V2 team, private qualifier record, final-OOS observation, or prospective record was
read.

Permitted governing sources read in full:

- `TOURNAMENT-CHARTER-TOP40-V2.md`
- `tournament/top40-v2/config.toml`
- `tournament/top40-v2/METHODOLOGY-DISTILLATION.md`
- `tournament/top40-v2/TEAM-PLAYBOOK.md`
- `tournament/top40-v2/PHASE0-POLICY.md`
- `.claude/agents/top40-v2-quant-researcher.md`

Own-namespace sources read:

- `tournament/top40-v2/teams/team-02/BOOTSTRAP.md`
- empty `families.jsonl` and `experiments.jsonl`
- initial disabled `risk_policy.json`

Neutral V2 interfaces inspected only to bind the registration/data/risk contract:

- family-registration validation and command dispatch in `scripts/top40_v2_tournament.py`
- `DecisionContext` timing contract in `src/crypto_trade/tournament/protocol.py`
- past-only worker streaming contract in `src/crypto_trade/tournament/_strategy_worker_v2.py`
- declarative control schema in `src/crypto_trade/tournament/risk_policy.py`
- neutral raw kline/funding column declarations and causal membership interface in
  `src/crypto_trade/tournament/snapshot.py` and `src/crypto_trade/tournament/data.py`

No snapshot bytes or market observations were opened. No `run-window`, evaluator, snapshot,
`register-trial`, result-recording, private, or final command was invoked during formation.

## Independent reasoning chain

The governing documents require causal availability, both sleeves, bull/bear/chop roles, stress
control, parameter stability, chronological OOF evidence, doubled-cost survival, and explicit
risk ablations. The family was built from those constraints and generic market microstructure
logic:

1. separate common market movement from cross-sectional residual movement;
2. condition persistence versus reversal on past-only path efficiency and breadth;
3. use realized funding as the directly paid crowding/carry variable;
4. preserve both sleeves while smoothly tilting gross toward the causal market direction;
5. treat volatility, drawdown, and turnover as separate organizer-owned controls with factorial
   ablations.

No empirical coefficient, historical winner, or observed period-specific target informed a
parameter. Ranges are deliberately coarse, economically interpretable, and bounded by the
available warmup. The planned 52 configurations leave 28 of the cumulative 80 unspent for at most
two genuinely documented pivots.

## Reproducibility commitments

- Canonical runtime/worker strategy seed: frozen config value `20260801`; it is the only seed used
  to generate production target weights.
- Team trial/search/tie-test namespace: `2026080102`; it may identify team-scoped records and test
  cases but is never passed as the worker seed or used as a production target seed.
- Feature cutoff: one completed 8-hour bar before every decision.
- Exact ties: average cross-sectional rank, then alphabetical symbol for set membership.
- No forward label, global scaler, prefitted opaque state, or timestamp-to-target table.
- Six contiguous chronological folds score every date in canonical
  `[2020-02-03, 2023-07-01)` exactly once. Earlier `[2020-01-01, 2020-02-03)` history is state-only
  warmup. A 30-day outcome-selection embargo does not remove scored dates.
- Every material change is registered before execution; negative and interrupted outcomes count.
- Source, parameters, risk subset, dependencies, seed, journal head, fold declarations,
  neighborhood, and evidence hashes freeze before the one private ticket.

## Mechanism-identity guardrail

The variable causal interaction between residual persistence and residual reversal is mandatory.
Trend-only, reversal-only, and fixed-blend arms remain diagnostic falsifiers and cannot be promoted
as this family's champion. An unconditional continuation strategy, a fixed `P`, or removal of the
reversal interaction requires a formal mechanism pivot before execution. This organizer
collision-control condition adds no information about any other mechanism.

## Pre-data numerical clarification

Before code, data access, or any trial, the QE completeness review identified executable degrees of
freedom that the qualitative preregistration did not numerically bind. They are now frozen without
changing the registered thesis or domain:

- binary64 arithmetic, natural log, deterministic ordered reductions, and `epsilon=1e-12` only in
  residual-z, ER, and direction denominators;
- population (`ddof=0`) covariance, variance, and standard deviation throughout;
- exact-grid count windows, complete displacement horizons, rational valid-history thresholds, and
  left-open/right-closed funding windows;
- exact average-rank mapping, clipped sigmoid/tanh inputs, neutral funding after valid-only ranking,
  and epoch-anchored rebalance boundaries;
- exact rational `q`, `K=max(4,floor(q*N))`, type-7 10th/90th volatility quantiles, and
  deterministic 9.5%-cap water filling with `1e-12` absolute weight tolerance.

These choices resolve implementation ambiguity only. Any later change is material for research
accounting. No market observation, evaluator result, other mechanism, or lifecycle command informed
the clarification.

## Pre-trial neutral-interface correction

Before code or any trial, organizer preflight established that the neutral worker's normalized
realized-funding context exposes `funding_time`, `symbol`, `funding_rate`, and `mark_price`, but not
interval metadata. The earlier prose formula's interval denominator was therefore non-executable.
It has been replaced with the exact interface-compatible statistic
`cumulative_funding = fsum(funding_rate)` over the already-frozen left-open/right-closed window,
ranked on its negative. `mark_price` is intentionally unused because the signal ranks per-notional
realized rates and the evaluator owns cashflow calculation. No fixed positive scale is applied
because it cannot change a cross-sectional rank.

The pre-existing minimum of two unique events is retained. A duplicate `(symbol,funding_time)` key
or any non-finite in-window rate makes that symbol's funding statistic invalid and neutral; valid
symbols are ranked only when at least four exist, otherwise all funding scores are neutral. This is
a neutral-interface correction within the registered realized-funding mechanism, not a
performance-driven choice, thesis/domain change, or pivot. `ablations.json` required no change: its
funding-removal diagnostic refers only to `w_funding` and contains no interval-dependent input or
formula.

## Mechanism fingerprint

The mechanism fingerprint is the SHA-256 digest of the exact bytes of
`family-registration.json` after JSON validation and before organizer registration:

`fbcbd302cc406c677a66dc3766ffe7f5ab00d7641f6ceb220535927735bf98c3`

The organizer-owned `families.jsonl` and research journal are not hand-edited.
