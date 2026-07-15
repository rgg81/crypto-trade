# Top-40 Crypto Futures Research Tournament V2

This charter creates ten independent teams and a variable-size finalist cohort. Each team has a
Quantitative Researcher and Quantitative Engineer, may research up to three preregistered mechanism
families, and may freeze a champion only after passing fixed development and private qualification
gates. V2 reuses the proven V1 Binance data and execution foundation by hash but inherits no V1
strategy, report, result, parameter, or research conclusion.

## 1. Objective

Find a reproducible, cost-aware long/short Top-40 crypto-futures portfolio that:

- demonstrates strong chronological out-of-fold development performance;
- survives one private qualification window before becoming a finalist;
- generalizes to a single sealed final-OOS reveal;
- has useful behavior in bull, bear, chop, and stress conditions;
- uses both long and short sleeves in economically meaningful roles;
- controls drawdown and tail exposure with causal, executable risk policies; and
- can proceed unchanged to prospective paper observation.

The tournament does not manufacture a finalist or winner when no model meets its qualification
standard. Rank and readiness for capital are separate conclusions.

## 2. Strategic clean room

V2 teams may read this charter, the V2 config and methodology, their V2 agent definition, neutral
V2 evaluator interfaces, generic statistical references, and the authorized visible-development
view. They may not read V1 team namespaces, V1 reports, V1 ballots, V1 leaderboards, historical
portfolio strategies, another V2 team, private-qualifier records, or final-OOS data.

Before material experiments, each mechanism family records its independent origin, economic
thesis, causal feature lineage, expected regime roles, falsifier, parameter ranges, selection
metric, risk policy, and trial allocation. Collision detection may force a redraw without revealing
another team's mechanism.

## 3. Windows and visibility

- Visible development: `[2020-02-03, 2023-07-01)` UTC.
- Private qualifier: `[2023-07-01, 2024-07-01)` UTC.
- Final OOS: `[2024-07-01, 2026-07-01)` UTC.
- Prospective paper: begins at the first 8h boundary after winner freeze.

Visible development is selection-touched. Its qualification metrics must be stitched from
chronological out-of-fold predictions. The private qualifier has one frozen ticket and releases
only pass/fail plus failed gate names until the finalist cohort locks. Final OOS is revealed once,
after every team is terminal and the finalist cohort is committed.

Because V1 already used the final-OOS interval, V2 describes it as sealed from fresh competitors,
not globally untouched. Prospective paper remains the first untouched evidence.

## 4. Common market, universe, and execution contract

V2 uses the exact SHA-bound V1 public-Binance USD-M snapshot unless Phase 0 explicitly builds and
binds a replacement. The point-in-time weekly Top-40 universe, historical delisting behavior,
actual funding rows and signs, next-open fills, participation cap, 5 bp fee, 2.5 bp slippage,
unlevered exposure limits, and independent doubled-cost rerun remain unchanged.

The central evaluator, never team code, owns fills, costs, funding cashflows, positions, equity,
entry basis, drawdown, risk actions, delistings, and scores.

## 5. Research lifecycle

Ten teams begin in `researching`. A team may use its initial mechanism and at most two documented
pivots. Pivots do not reset the cumulative 80-configuration, 12-CPU-hour, 18-wall-hour, or deadline
budgets.

The organizer provides an exact IS-only evaluator that cannot load or reveal later windows. Every
material candidate is registered before execution and appended to both the team ledger and the
organizer hash-chain journal. Failed, abandoned, manually selected, ensemble, feature, parameter,
and risk-control variants all count.

A team that cannot meet the development gate continues, pivots, or records DNF. `qr_accepted=false`
and a failed selector can never be mechanically advanced.

## 6. Development qualification

Qualification uses centrally generated canonical artifacts and the thresholds frozen in
`config.toml`. At minimum it requires:

- OOF net Sharpe at least 0.75;
- positive annualized return;
- Calmar at least 0.40 and drawdown at most 30%;
- doubled-cost Sharpe at least 0.35;
- at least four of six positive chronological folds;
- at least 55% positive quarters;
- trial-adjusted probability of positive Sharpe at least 90%;
- stable neighboring parameters rather than an isolated optimum;
- limited fold/quarter PnL concentration;
- required bull, bear, chop, stress, sleeve-role, and materiality gates.

All gates are binary and non-compensatory. Critic, user, or relative ranking points cannot make an
unqualified team a finalist.

## 7. Private qualification and finalist freeze

After visible qualification, the team freezes source, parameters, seeds, dependency lock, risk
policy, trial ledger, parameter-neighborhood declaration, and evidence hashes. It then consumes
its only private-qualifier ticket. The worker replays all authorized prior history for stateful
learning but scores only the private window.

Passing requires the frozen private thresholds. Failure is terminal DNF. Detailed private metrics
stay organizer-sealed until qualification closes. `close-qualification` makes every unresolved team
a deadline DNF and binds all qualified and DNF records. `lock-finalist-cohort` first-adds the exact
variable-size finalist cohort. Zero finalists ends as `no_qualified_model`.

## 8. Risk policies

V2 supports organizer-owned declarative risk controls using authoritative portfolio state.
Permitted controls initially include volatility targeting, portfolio drawdown brakes,
close-confirmed position stops, time stops, loss cooldowns, side scaling, turnover limits, and
centrally enforced exposure limits.

With 8h bars, no policy receives an intrabar fill. Funding is charged to the carried position,
risk is evaluated from known boundary state, and any reduction fills at the next open with ordinary
costs and participation limits. Same-boundary reopening is disabled unless explicitly frozen.
Every submitted control requires no-control, individual, combined, and doubled-cost ablations.

## 9. Regimes and sleeve roles

The one-day-lagged common BTC labels remain fixed. Development must have positive net return in
bull, bear, and chop; at least three regimes must have positive Sharpe; worst-regime Sharpe must be
at least -0.25. Stress may be approximately flat but cannot violate drawdown or tail-risk limits.

Long attribution must be positive in bull, short attribution positive in bear, and the combined
portfolio positive in chop. Both sleeves must satisfy the stronger V2 realized exposure and
notional floors. Every sleeve-by-regime attribution is published, but every cell need not be
positive.

## 10. Final OOS and scoring

Every finalist consumes exactly one organizer final-OOS reveal. Inside that sealed reveal, the
organizer performs two independent clean-process replays and requires identical metric records
and artifact hashes before promoting one canonical result. Teams receive zero final-OOS views
before the selection lock. A disappointing OOS result is not an integrity DQ; it is the
experiment's answer and receives low automatic points.

Final score remains 70 automatic, 15 Critic, and 15 user. Of the automatic score, 50 points use
fixed absolute bands and 20 use cohort-relative ranks. Negative OOS Sharpe and nonpositive
doubled-cost Sharpe receive no absolute points for those components. Absolute scoring prevents a
weak cohort from appearing economically strong merely through percentile ranks.

The frozen 50-point absolute score is: 15 final-OOS Sharpe, 10 drawdown, 8 doubled-cost Sharpe,
5 annualized return, 3 positive-quarter fraction, 4 regime robustness, and 5 cross-window/
role/parameter stability. The 20 relative points are: 7 final-OOS Sharpe, 4 drawdown, 3
doubled-cost Sharpe, 2 annualized return, 2 worst-regime Sharpe, and 2 cross-window/role/stability.
All bands, subweights, average-rank tie handling, sole-finalist treatment, and six-decimal rounding
are frozen in `config.toml` before research.

DNF teams appear in the final report with their research disposition and failed gates but receive
no fabricated OOS, Critic, user, or total score.

## 11. Integrity review and paper eligibility

The Critic scores every finalist from 0–3 in each frozen category: `data_integrity`,
`execution_realism`, `reproducibility_provenance`, `research_discipline`, and `risk_disclosure`.
The complete 0–15 Critic ballot locks before the user ballot.

Integrity DQs remain restricted to demonstrated failures using one of six codes:
`data-boundary-violation`, `execution-contract-violation`, `provenance-failure`,
`evaluator-tampering`, `reproducibility-failure`, or `source-freeze-mismatch`. Every allegation
cites exact artifact bytes and has no effect until independently confirmed. Performance is not an
integrity DQ. If all finalists would be DQed, selection stops at `integrity_review_required`.

The user ballot assigns an explicit 0–15 score to every original finalist, including one later
DQed. `lock-selection` combines the already-locked automatic score, complete ballots, and confirmed
DQ codes without recomputing objective scores. Automatic scores and objective ranks survive a
later integrity DQ; the DQed entry has no final total or final rank.

Paper eligibility is separately mechanical and uses the higher frozen development, private,
final-OOS, cost, drawdown, quarter, and regime thresholds. At least one qualified finalist may win
the tournament while nobody is ready for paper trading.

Winner freeze creates a prospective paper-journal genesis at the next 8h boundary, records a
three-boundary quarantine, and keeps `live_orders_enabled=false`. Paper evidence is the first
globally untouched validation for V2.

## 12. V2 immutability

V2 lives under `tournament/top40-v2/`, `reports-top40-v2/`, V2-specific source modules, and
`scripts/top40_v2_tournament.py` on branch `quant-portfolio-blind-top40-v2`. V1 frozen files are not
modified. V2 Phase 0 binds the shared snapshot bytes and all V2-specific rules and code before any
team dispatch.
