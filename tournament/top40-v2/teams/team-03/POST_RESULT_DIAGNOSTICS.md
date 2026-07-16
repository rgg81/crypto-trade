# Team 03 post-result diagnostics

Status: terminal development failure for `t03-rlsa-base-h3-b30-v21-f25`; no promoted result
artifacts.

## Auditable evidence

The Team 03 journal records one registered material candidate and one terminal result:

| Field | Recorded value |
| --- | --- |
| Family | `t03-residual-liquidity-shock-absorption-v1` |
| Candidate | `t03-rlsa-base-h3-b30-v21-f25` |
| Registration | `2026-07-16T10:37:15Z` |
| Registration SHA-256 | `f295e81e2cb443659de88d41370a97cba69cb21beaa4e031a9d3c3a62c05428e` |
| Result | `failed` |
| Failure | `ValueError: portfolio insolvent at 2022-05-13 00:00:00+00:00` |
| Result recorded | `2026-07-16T11:20:12.508078Z` |
| CPU / wall-clock use | `0.1956536004` / `0.1955250685` hours |
| Artifact hashes | empty object |
| Metrics summary | empty object |

The failure boundary lies inside the preregistered fourth fold, whose test interval was
2021-11-01 through 2022-05-31. This only localizes the terminal event; it is not evidence about
fold return, a particular instrument, or either sleeve.

Before registration, the current source revision passed five Team 03 synthetic checks and the
no-control risk-policy schema validation. Those checks establish deterministic and causal fixture
behavior, not portfolio viability.

## What the result establishes

- The evaluator reached a state it classified as portfolio insolvency.
- Insolvency is an explicit immediate falsifier in the registered trial.
- The candidate cannot qualify, be promoted, be rerun, or be repaired in place.
- The base did not pass the activation condition for its parameter neighborhood or risk-control
  ablations.
- Empty metric and artifact payloads mean there is no admissible Sharpe, return, drawdown, fold,
  quarter, regime, sleeve, turnover, or cost result to interpret.

## What the result does not establish

There is no evidence identifying the losing symbol, long or short sleeve, funding contribution,
turnover path, fill-capacity effect, or market narrative around the failure date. No such account
may be reconstructed from hindsight or external data. It is also invalid to treat absent fold or
regime metrics as passes.

The original brief explicitly identified falling-knife and squeeze continuation as a stress risk.
It is therefore reasonable to pose a new, falsifiable mechanism question: does observed
post-shock absorption need to precede entry? This is a hypothesis motivated by the ex-ante
mechanism caveat and the terminal insolvency, not a claimed diagnosis of the hidden path.

## Accounting consequence

The failed configuration and its consumed CPU/wall time remain charged to Team 03. The old family
and candidate records remain immutable. Any successor is a new child family, consumes one of the
two allowed mechanism pivots, requires registration before measurement, and receives new hashes.
