# Team 04 UTC reference 001: visible-development gate review

Date: 2026-07-16  
Decision basis: runner record, frozen Team 04 development artifacts, Team 04 preregistration, and
public Top-40 V2 config/methodology only

Status meanings:

- **PASS**: the exact required value is present or directly derivable from allowed artifacts.
- **FAIL**: the exact value violates the gate, or the preregistration explicitly defines its
  unavailable state as failure.
- **NOT EVIDENCED**: a required value is absent and this local review cannot certify it.
- **NOT REACHED**: the family stop rule prevents the later study that would create the value.

## Exact preregistered initial-family falsifier

The exact no-control reference must stop before parameter, neighbor, or risk study if it is
insolvent or incomplete; has nonpositive annualized return, net Sharpe, or doubled-cost Sharpe;
has fewer than four profitable folds; has nonpositive bull, bear, or chop return; fails long-bull
or short-bear attribution; or lacks positive pooled score IC and positive score IC in at least four
of six folds. Controls cannot rescue a failed core. Team 04's local `ablations.json` further says to
stop before every later observation if the reference fails completeness, solvency, aggregate,
cost, fold, regime, sleeve, or score-IC falsifiers.

## Aggregate and chronological gates

| Gate | Threshold | Exact evidence | Status |
|---|---:|---:|---|
| Runner completion | completed, no failure | `completed`; `failure_reason=null` | **PASS** |
| Solvency | terminal equity `> 0` | `202281.04490110261` base; `183754.22694256049` doubled cost | **PASS** |
| Annualized return | prereg `> 0`; public `>= 0` | `0.22961686194837383` | **PASS** |
| Net Sharpe | prereg `> 0`; public `>= 0.75` | `1.5251401450635822` | **PASS** |
| Calmar | `>= 0.40` | `1.4397252448816922` | **PASS** |
| Maximum drawdown | `<= 0.30` | `0.15948658451650777` | **PASS** |
| Doubled-cost Sharpe | prereg `> 0`; public `>= 0.35` | `1.326264500422908` | **PASS** |
| Profitable folds | `>= 4/6` | `4/6` | **PASS**, exactly at floor |
| Positive quarters | `>= 0.55` | `0.5 = 7/14` | **FAIL** |
| Trial-adjusted probability positive | `>= 0.90` | not present | **NOT EVIDENCED** |

The status-completion row has one disclosed caveat: the last base bar contains
`7582.3394910577117` USDT of terminal unresolved notional. The runner does not classify that as a
failure or interruption, so this local review does not override its completed status.

The six base fold returns are, chronologically:

1. `0.008980839704992194`
2. `0.78752574440227385`
3. `0.069892487450346819`
4. `0.070564916556517421`
5. `-0.02067350362457121`
6. `-0.00013972493594172075`

## Regime and economic-role gates

| Gate | Threshold | Exact evidence | Status |
|---|---:|---:|---|
| Bull net return | `> 0` | runner publishes Sharpe only | **NOT EVIDENCED** |
| Bear net return | `> 0` | runner publishes Sharpe only | **NOT EVIDENCED** |
| Chop net return | `> 0` | runner publishes Sharpe only | **NOT EVIDENCED** |
| Positive-Sharpe regimes | `>= 3` | `4/4` | **PASS** |
| Worst regime Sharpe | `>= -0.25` | bear `0.7867376412555669` | **PASS** |
| Long-bull net return | `> 0` | not present | **NOT EVIDENCED** |
| Short-bear net return | `> 0` | not present | **NOT EVIDENCED** |
| Combined-chop net return | `> 0` | not present | **NOT EVIDENCED** |

Published Sharpes are bull `1.8164528189119538`, bear `0.7867376412555669`, chop
`2.5636916917000785`, and stress `1.3266068181061883`. Positive Sharpe supports the thesis but is
not substituted for the schema's separately required compounded regime and role returns.

## Sleeve-activity gates

An active side is evaluated at the public `0.01` exposure floor.

| Gate | Threshold | Long | Short | Status |
|---|---:|---:|---:|---|
| Active-bar fraction | `>= 0.10` | `0.680064308681672` | `0.680064308681672` | **PASS** |
| Mean gross exposure | `>= 0.01` | `0.19732607399648086` | `0.19371585845223049` | **PASS** |
| Executed notional | `>= 1000` USDT | initial open `24005.77364747403` | initial open `24009.678539455334` | **PASS** |

The initial opening rebalance is a conservative lower bound, not the cumulative sleeve total. It
is enough to establish each notional floor without reconstructing later position state.

## Stability and concentration gates

| Gate | Threshold | Exact evidence | Status |
|---|---:|---:|---|
| Profitable-neighbor fraction | `>= 0.70` | neighborhood status `preregistered-not-run` | **NOT REACHED** |
| Neighbor median Sharpe | `>= 0.50` | no neighbor results | **NOT REACHED** |
| Maximum positive-PnL concentration | `<= 0.40` | official value absent | **NOT EVIDENCED** |

The declared neighborhood requires at least seven profitable cells among the center plus eight
neighbors and median Sharpe at least `0.50`. Those runs must not be started after the initial-family
stop trigger. Direct diagnostic proxies are adverse: the largest positive-fold share is
`0.8405080178026505`, and the largest positive-quarter share is `0.46764717373054659`. These are
not relabeled as the missing official metric.

## Team 04 causal score gate

| Gate | Threshold | Exact evidence | Status |
|---|---:|---:|---|
| Pooled next-holding-period score IC | `> 0` | unavailable | **FAIL by preregistration** |
| Positive fold score IC | `>= 4/6` | unavailable | **FAIL by preregistration** |

The runner has no score-IC section, and the persisted target artifact contains target weights but
not the composite score needed for the preregistered forward diagnostic. The review instruction
and Team 04 preregistration treat unavailable score IC like a nonpositive value, so this is a hard
family falsifier rather than an invitation to continue and inspect more cells.

## Audit and qualification conclusion

- Registration precedes reservation and result; exact hashes match across the records.
- The run uses the exact no-control reference and the correct development window.
- The six folds are the preregistered chronological folds.
- The public positive-quarter gate fails directly.
- Trial-adjusted probability, exact regime returns, economic-role returns, and official PnL
  concentration are absent, so a complete development qualification cannot be certified.
- Neighborhood stability is intentionally not reached after the family stop.
- Most importantly, unavailable pooled and fold score IC triggers the exact Team 04 family stop.

Overall visible-development result: **FAIL / NOT QUALIFIED**. This is negative research evidence,
not a candidate for a private-qualifier ticket.
