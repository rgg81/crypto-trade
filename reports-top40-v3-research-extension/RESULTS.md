# Top40 V3 post-tournament research extension results

Status: complete  
Study: `top40-v3-post-tournament-team04-team06-r1`

## Evaluation windows

- Development IS: 2020-02-03 through 2023-06-30
- Blind qualifier: 2023-07-01 through 2024-06-30
- One-shot blind final: 2024-07-01 through 2026-06-30

The qualifier intentionally releases only pass/fail. Its private returns and metrics
remain sealed. Only qualifier passers are evaluated in the final.

## Outcome

| Team | Frozen candidate | Development | Qualifier | Final |
|---|---|---:|---:|---:|
| Team 04 | `t04-utc-r1-weekly-buffer` | Ready | Failed | Not evaluated |
| Team 06 | `t06-mom-r1-3d-persist` | Ready | Passed | Released |

## Development IS finalists

| Metric | Team 04 | Team 06 |
|---|---:|---:|
| Cumulative return | 86.71% | 111.66% |
| Annualized return | 20.11% | 24.61% |
| Net Sharpe | 1.430 | 1.414 |
| Net Sortino | 2.358 | 2.207 |
| Maximum drawdown | 11.26% | 11.55% |
| Double-cost annualized return | 18.60% | 22.22% |
| Double-cost Sharpe | 1.335 | 1.301 |
| Double-cost maximum drawdown | 11.68% | 11.94% |
| Annualized one-way turnover | 16.94x | 22.93x |
| Gross edge / one-way turnover | 119.90 bps | 109.15 bps |
| Cost share of positive gross PnL | 6.25% | 6.87% |
| Trades | 2,526 | 14,794 |
| Positive-quarter fraction | 64.29% | 78.57% |

Both finalists passed every frozen development gate before their code and source
bundles were frozen.

## Team 06 blind final OOS

| Metric | Base costs | Double costs |
|---|---:|---:|
| Cumulative return | 6.25% | 1.76% |
| Annualized return | 3.08% | 0.88% |
| Net Sharpe | 0.292 | 0.132 |
| Net Sortino | 0.418 | 0.187 |
| Maximum drawdown | 11.03% | 12.19% |
| Calmar | 0.279 | 0.072 |
| Positive-quarter fraction | 50.00% | 50.00% |

Final diagnostics:

| Diagnostic | Value |
|---|---:|
| Annualized one-way turnover | 25.35x |
| Gross edge / one-way turnover | 23.04 bps |
| Base cost share of positive gross PnL | 32.56% |
| Average gross exposure | 28.82% |
| Trades | 9,660 |
| Gross PnL | 11.68% |
| Long gross PnL | -4.44% |
| Short gross PnL | 16.11% |
| Risk-policy turnover fraction | 19.46% |

Final regime Sharpe was 0.365 in bull, 0.194 in bear, 0.354 in chop, and -1.267
in stress.

## Interpretation and disposition

Team 06 remained profitable at both base and double costs, so the blind result is
not a collapse to negative performance. It is nevertheless too weak for capital
deployment. Relative to development, base Sharpe fell about 79%, double-cost
Sharpe fell about 90%, and gross edge density fell about 79%, while annualized
turnover rose about 11% and costs consumed 4.7 times the prior share of positive
gross PnL. The final edge density of 23.04 bps is also below the extension's 30 bps
development floor. All final gross profit came from the short side, and the stress
regime was materially negative.

Disposition: preserve Team 06 unchanged as a research benchmark and run it only
in shadow/paper mode from the next predeclared live-forward boundary. Do not tune
against this final window and do not promote it to funded trading. Team 04 remains
a development result with a failed blind qualifier and no final score.

## Audit anchors

- Public final release: `final-oos/final-release.json`
- Release SHA-256: `e9cc66596de1ccf659505eb3f1ddfd2d544b41f9712d1900dbc23f95e5e8f634`
- Final journal record SHA-256: `44d7de0920af3ee4ff787c54a1c776186e10adc16fc6f0b12ca271c814a52fdc`
- Team 06 frozen source bundle SHA-256: `cd4c3c3b3b0815145d599e36a2ee93d330e51c7d3e6927c17c535e34684f5376`
- Team 04 frozen source bundle SHA-256: `c5b6fe65c954d15f17c6fb549e66513f3c0f2208ecdec0b8ec3612be59440a49`
