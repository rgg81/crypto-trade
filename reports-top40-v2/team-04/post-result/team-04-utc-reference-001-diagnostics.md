# Team 04 UTC reference 001: post-result diagnostics

Date: 2026-07-16  
Candidate: `team-04-utc-reference-001`  
Family: `team-04-uncrowded-trend-carry-v1`  
Scope: Team 04 visible-development artifacts only

This is a Team 04 local, read-only post-result diagnostic. It is not organizer-derived
qualification evidence and does not mutate tournament state. No strategy, evaluator, test,
tournament command, or Git operation was run. Derived values below are direct reductions of the
candidate's frozen CSV artifacts; Parquet inspection was limited to persisted schema metadata.

## Record identity and chronology

- Family registered: `2026-07-16T11:24:27Z`.
- Trial registered: `2026-07-16T11:26:51Z`.
- Development run reserved: `2026-07-16T11:28:16.395970+00:00`.
- Result recorded: `2026-07-16T11:39:42.938574Z`.
- Runner status: `completed`; failure reason: `null`.
- Scored interval: `2020-02-03` through `2023-06-30`, matching the visible-development split.
- Decisions: `3,732`; events: `81,443`; trade rows: `5,775`.
- Trial resource use: `0.18941028564249998` CPU hours and
  `0.18925009214777674` wall-clock hours.
- Seed: `20260801`.
- Strategy SHA-256:
  `0e63f868f99684bef394bc1996a6034032c0657b76eceefc1b1b052fdd0e02cc`.
- Config SHA-256:
  `bd0e4f70bcf335b2ac4e44ec049b89b8e8eaf4c6ac6502574d0accf12d9d9947`.
- Risk-policy SHA-256:
  `850e792495dd1861fbf61377d3131e4b43ecf3794b2f9545f6b9897c184b0fd2`.
- Source-bundle SHA-256:
  `8c3ba47894bbc45664ee1d7e56190f64e2c1dee1e8a9c749d4f0ec3344443520`.

The four hashes agree across registration, reservation, runner record, and the Team 04 trial
ledger. The frozen policy is the exact preregistered no-control policy: volatility targeting,
drawdown brakes, position/time stops, turnover limits, and side scaling are disabled.

## Runner aggregate

| Metric | Exact value |
|---|---:|
| Annualized return | `0.22961686194837383` |
| Net Sharpe | `1.5251401450635822` |
| Net Sharpe 95% interval | `[0.5167053393391644, 2.514129088247196]` |
| Net Sortino | `2.448755481977454` |
| Calmar | `1.4397252448816922` |
| Maximum drawdown | `0.15948658451650777` |
| Doubled-cost Sharpe | `1.326264500422908` |
| Doubled-cost Sharpe 95% interval | `[0.3135786607873179, 2.3196205126210647]` |
| Positive-quarter fraction | `0.5` (`7/14`) |

Direct daily compounding gives a base terminal multiple of `2.0228104490110326` and return of
`1.0228104490110326`. The doubled-cost terminal multiple is `1.8375422694256172`, for a return of
`0.83754226942561716`. These agree with the last bar equities of
`202281.04490110261` and `183754.22694256049` from `100000` initial equity.

The first nonzero daily return is `2020-08-21`. Of `1,244` scored daily rows, `369` are exactly
zero and `875` are nonzero. Thus the aggregate result includes a long initial inactive period,
including flat 2020 Q1 and Q2.

## Chronological folds

Fold return is the direct product `product(1 + daily net return) - 1` over each preregistered,
end-exclusive interval. Four of six base-cost folds are profitable, exactly meeting the family and
public minimum; folds 5 and 6 are negative. Doubled costs preserve the same four-positive/two-negative
pattern.

| Fold | Interval | Days | Base return | Doubled-cost return | Base profitable |
|---|---|---:|---:|---:|---|
| 1 | `[2020-02-03, 2020-09-01)` | 211 | `0.008980839704992194` | `0.0076549317662424343` | yes |
| 2 | `[2020-09-01, 2021-04-01)` | 212 | `0.78752574440227385` | `0.75324171501707182` | yes |
| 3 | `[2021-04-01, 2021-11-01)` | 214 | `0.069892487450346819` | `0.046585592690316702` | yes |
| 4 | `[2021-11-01, 2022-06-01)` | 212 | `0.070564916556517421` | `0.050906033434827913` | yes |
| 5 | `[2022-06-01, 2023-01-01)` | 214 | `-0.02067350362457121` | `-0.038028016228526917` | no |
| 6 | `[2023-01-01, 2023-07-01)` | 181 | `-0.00013972493594172075` | `-0.016934066409453497` | no |

The concentration is visibly adverse even before an official concentration statistic is
available. Using positive fold compounded returns as a disclosed diagnostic proxy, fold 2 supplies
`0.8405080178026505` of their sum. Using positive quarter compounded returns, 2021 Q1 supplies
`0.46764717373054659` of their sum. Neither proxy is substituted for the organizer's required
`maximum_positive_pnl_concentration` metric.

## Quarters

Direct daily compounding produces seven positive quarters out of fourteen. Zero-return quarters
are nonpositive for this gate.

| Quarter | Return | Positive |
|---|---:|---|
| 2020 Q1 | `0` | no |
| 2020 Q2 | `0` | no |
| 2020 Q3 | `0.038864337355833278` | yes |
| 2020 Q4 | `0.19866802551198282` | yes |
| 2021 Q1 | `0.44836314748313022` | yes |
| 2021 Q2 | `0.082499072127849127` | yes |
| 2021 Q3 | `-0.064453929383964326` | no |
| 2021 Q4 | `0.12612050083666304` | yes |
| 2022 Q1 | `-0.021399043998967193` | no |
| 2022 Q2 | `-0.0015903148616833729` | no |
| 2022 Q3 | `-0.045609054996557763` | no |
| 2022 Q4 | `0.054781106704224536` | yes |
| 2023 Q1 | `-0.0095171584516958729` | no |
| 2023 Q2 | `0.0094675375709649678` | yes |

## Regimes and roles

The runner publishes regime Sharpe but not regime net returns or regime-by-sleeve attribution.

| Regime | Runner Sharpe |
|---|---:|
| Bull | `1.8164528189119538` |
| Bear | `0.7867376412555669` |
| Chop | `2.5636916917000785` |
| Stress | `1.3266068181061883` |

All four Sharpes are positive and the worst is bear at `0.7867376412555669`. This proves the two
Sharpe gates from the runner record. It does not supply the separately required bull, bear, and
chop net returns, long-bull return, short-bear return, or combined-chop return. The allowed CSVs
contain no regime label, so those exact role metrics cannot be reconstructed without invoking data
or evaluator paths that are outside this review.

## Sleeves, funding, and execution costs

Direct reduction of `bar_returns.csv` over all `3,732` bars gives:

- Long exposure at or above `0.01`: `2,538/3,732 = 0.680064308681672`.
- Short exposure at or above `0.01`: `2,538/3,732 = 0.680064308681672`.
- Mean long gross exposure: `0.19732607399648086`.
- Mean short gross exposure: `0.19371585845223049`.
- The first opening rebalance has six longs totaling `24005.77364747403` USDT and six shorts
  totaling `24009.678539455334` USDT, independently exceeding the `1000` USDT executed-notional
  floor for both sleeves.

The base-cost additive bar-return attribution is:

| Component | Exact additive contribution |
|---|---:|
| Long price PnL | `0.95400691873902066` |
| Long funding PnL | `-0.057424409105826239` |
| Long pre-cost total | `0.89658250963319441` |
| Short price PnL | `-0.22143217626534939` |
| Short funding PnL | `0.15320139888744447` |
| Short pre-cost total | `-0.068230777377904922` |
| Net funding PnL | `0.095776989781618596` |
| Fees | `0.064160217115911508` |
| Slippage | `0.032080108557955754` |
| Net additive return | `0.73211140658142104` |

Funding therefore helps materially and comes entirely from the short-side net benefit, but it does
not make the short sleeve positive across the full development interval. The long sleeve supplies
the entire positive pre-cost sleeve result. This whole-window attribution cannot replace the
required short-bear role metric.

The trade artifact records `11643.483068493713` USDT of fees and `5821.7415342468566` USDT of
slippage, totaling `17465.224602740571` USDT. At doubled costs, additive fees are
`0.12833975038006656` and slippage is `0.064169875190033282`; doubled-cost additive net return is
`0.6360797247288249`. The runner's doubled-cost Sharpe remains `1.326264500422908`.

The last base-cost bar reports `7582.3394910577117` USDT of terminal unresolved notional; the
doubled-cost last bar reports `6910.5823082235693`. The runner nevertheless records the run as
completed with no failure reason, and terminal equity remains positive. This review treats the
run as status-complete and solvent while retaining the unresolved terminal notional as an
execution caveat, not silently relabeling it.

## Score-IC availability

The preregistration requires pooled composite-score IC greater than zero and positive composite
score IC in at least four of six folds against the next scheduled three-day return. No pooled or
fold IC appears in the runner or Team 04 result ledger. Persisted `targets.parquet` schema metadata
contains only `timestamp`, `__crypto_trade_rebalance__`, and per-symbol target weights; it does not
contain the preregistered composite score. The required score/forward-label pairs therefore cannot
be formed from the allowed artifacts.

Exact pooled score IC: **unavailable**.  
Exact number of positive-IC folds: **unavailable**.

Per the preregistered Team 04 rule supplied for this review, nonpositive or unavailable score IC is
a falsifier failure.

## Stale pre-result declarations

`BOOTSTRAP.md`, `research_brief.md`, `frozen_config.json`, and `test_evidence.json` still describe
the reference as not registered/not run or set `material_trial_run` to false. These statements were
valid pre-result declarations but are now stale relative to the append-only registration, result,
and runner records. They were not edited in this review.
