# Top-40 V3

Top-40 V3 is a new ten-team, pure-crypto tournament. Its central rule is simple: research is done
in a transparent training laboratory, validation access is scarce, and a team cannot formally
submit a model that is already nonpositive on training or validation.

The authoritative policy is [`../../TOURNAMENT-CHARTER-TOP40-V3.md`](../../TOURNAMENT-CHARTER-TOP40-V3.md).
The operational team guide is [`TEAM-PLAYBOOK.md`](TEAM-PLAYBOOK.md), and machine-readable policy
defaults are in [`config.toml`](config.toml). If prose and configuration disagree, the charter is
authoritative and activation MUST stop until the conflict is resolved before any result is run.
The latest primary-source search and frozen-data feasibility decisions are recorded in
[`RESEARCH-SCOUTING-2026.md`](RESEARCH-SCOUTING-2026.md). The four historical V2 ports and their
shared-budget rules are defined in
[`INCUMBENT-CHALLENGER-POLICY.md`](INCUMBENT-CHALLENGER-POLICY.md).

## What is new

- Top-40 V2 remains immutable; V3 uses new journals, locks, reports, and results.
- Four provenance-bound V2 passers start as grandfathered incumbents in their original teams.
  They receive no inherited result or automatic qualification and consume ordinary V3 trial,
  probe, and nomination budgets.
- The exact A6-audited weekly universe is reused read-only and fails closed to native crypto.
  Stablecoins, TradFi, equities, ETFs, metals, commodities, indexes, FX, and leveraged tokens are
  ineligible even if Binance lists a perpetual contract.
- Training runs are unlimited but every material trial and failure is permanently logged before
  metrics are returned.
- Each team receives three opening sealed-validation probes and at most one formal nomination.
  If the comeback triggers, an unqualified team receives exactly two additional logged probes.
- A nominee must be strictly positive in net Sharpe, annualized return, and doubled-cost Sharpe on
  both training and validation, pass all hard gates, and be identical to its probed candidate.
- Public advancement requires the fixed performance core and is ordered by a fixed robustness
  score. Diagnostic evidence is scored and disclosed, never used as a hidden veto.
- A predeclared comeback lab round opens only when fewer than three teams have a public-core
  passer; it adds two logged probes for eligible teams but never lowers a floor.
- Private qualification is deliberately simple. Final OOS is revealed once, simultaneously.

## Lifecycle

```text
visible train labs -> <=3 sealed probes -> [optional comeback: +2] -> one nominee/team
       -> hard gates + public core -> robustness rank -> top 4 (or all if fewer)
       -> one private gate -> one simultaneous final-OOS reveal
```

## Grandfathered incumbent lane

Teams 04, 05, 07, and 09 each retain one lean historical port as a training-lab benchmark. Every
port must independently earn positive training and validation results and pass the same hard gates
as a new design. A challenger supersedes the incumbent only on standardized logged V3 evidence;
each team still has one shared probe budget and at most one nominee. Collision guards govern new
designs but do not retroactively erase the four explicitly disclosed historical incumbents. See
the [incumbent/challenger policy](INCUMBENT-CHALLENGER-POLICY.md) for exact candidate paths and
lineage rules.

The frozen scored windows are:

| Stage | Dates (UTC, inclusive) | Feedback |
| --- | --- | --- |
| Training | 2020-02-03 to 2022-06-30 | full data and standardized metrics |
| Sealed validation | 2022-07-01 to 2023-06-30 | fixed aggregate packet; no raw observations |
| Private qualifier | 2023-07-01 to 2024-06-30 | one pass/fail decision after public selection |
| Final OOS | 2024-07-01 to 2026-06-30 | one simultaneous reveal |

## Public core

Every hard gate must pass first. The concatenated train-plus-validation record then requires:

| Net Sharpe | Annual return | Drawdown | 2x-cost Sharpe | Positive quarters | Trades | Positive regimes | Worst regime |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `>=0.75` | `>0` | `<=0.30` | `>=0.35` | `>=0.50` | `>=1000` | `>=2/4` | `>=-0.75` |

Among core passers, with `C(x)=min(1,max(0,x))`:

```text
R = 25*C((net_sharpe-0.75)/0.75)
  + 15*C(annualized_return/0.30)
  + 15*C((0.30-max_drawdown)/0.20)
  + 15*C((double_cost_sharpe-0.35)/0.65)
  + 15*C((positive_quarter_fraction-0.50)/0.25)
  + 10*(positive_regime_count/4)
  +  5*C((worst_regime_sharpe+0.75)/1.50)
```

`R` ranks passers; it is not another gate. The top four advance, or all passers if fewer than
four exist.

## Activation boundary

The V3-only organizer entrypoint is active for policy validation, Phase-0 freeze, status, and
transparent training labs. Before the first lab result, Phase 0 must independently test and
hash-freeze the implementation, metric schema, diagnostic rubric, append-only journal, schedule,
seeds, active entrypoint, and organizer-owned sandbox canary under the V3 namespace. The canary
must complete one synthetic decision through the real namespaced worker and clean shutdown; it
never reads the market snapshot or consumes a team trial. Sealed validation, private
qualification, and final OOS are intentionally absent from this entrypoint. No V2 dispatcher or
result authority is repurposed as V3 state.
