# Team 03 first iteration — residual liquidity-shock absorption

Status: preregistration draft; no evaluator or tournament command has been run.

## Independent mechanism

Family ID: `t03-residual-liquidity-shock-absorption-v1`

Initial candidate ID: `t03-rlsa-base-h3-b30-v21-f25`

Crypto perpetual markets periodically absorb forced directional flow from liquidations, crowded
funding, and mandate-constrained deleveraging. When an individual contract moves much farther than
its contemporaneous BTC beta predicts, and that move arrives with exceptional quote volume, some
of the price change should be temporary impact rather than information. Persistent funding on the
same crowded side strengthens that interpretation.

The strategy therefore ranks a past-only idiosyncratic shock-exhaustion score once daily:

1. estimate each eligible contract's rolling beta to BTC from 8-hour close-to-close log returns,
   ending the beta baseline immediately before the three-bar shock window;
2. sum the latest three beta residuals and scale by residual volatility estimated from the
   pre-shock baseline;
3. amplify only unusually high-volume shocks;
4. penalize positive funding and reward negative funding in the long-desirability score; and
5. buy the strongest negative exhaustion tail and short the strongest positive exhaustion tail.

BTC is an anchor, not a traded member of either cross-sectional sleeve. The implementation uses no
learned model, random choice, private data, current fill price, or future row.

## Causal feature lineage

| Feature | Raw public fields | Availability and lag | Missing-data rule |
| --- | --- | --- | --- |
| 8h log return | `open_time`, `close` | Candle must be fully closed by the decision | Symbol omitted if history is insufficient or non-finite |
| BTC beta residual | symbol and BTC closed returns | 30 baseline days ending before the three-bar shock window, recomputed at decision | Symbol omitted if aligned variance is degenerate |
| residual scale | past beta residuals | 21 baseline days ending before the three-bar shock window | Symbol omitted below frozen variance floor |
| volume surprise | `quote_volume` | latest completed 24h versus trailing 30-day median | Symbol omitted for invalid/nonpositive baseline |
| funding crowding | `funding_time`, `funding_rate` | rows strictly before decision; 3-day mean scaled by 30-day history | Neutral zero contribution until 12 valid events |
| BTC trend tilt | BTC closed returns | trailing 60 days | Symmetric sleeves until sufficient history |

The target decided at time `t` is filled by the central evaluator at the executable open timestamped
`t`; that open is not observed by the strategy.

## Sleeve and regime roles

- Long sleeve: contracts suffering unusually negative residual shocks, especially with heavy
  volume and negative funding. It should monetize forced-sale absorption and contribute positively
  during bull-market pullbacks.
- Short sleeve: contracts experiencing unusually positive residual shocks, especially with heavy
  volume and positive funding. It should monetize crowded squeeze exhaustion and contribute
  positively during bear-market relief rallies.
- Bull: a slow positive BTC trend moves 5% gross from short to long (`45%/35%`).
- Bear: a slow negative BTC trend moves 5% gross from long to short (`35%/45%`).
- Chop: symmetric `40%/40%` sleeves are the main expected source of return.
- Stress: both tails may reverse sharply, but falling-knife risk is material. The baseline stays
  unlevered and diversified; separately registered volatility/drawdown controls must demonstrate
  benefit without hiding a nonviable no-control signal.

## Frozen first candidate

The exact base parameters are in `candidate_spec.json` and `strategy.py`. It rebalances only at
`00:00 UTC`, requires at least 20 valid non-BTC contracts, selects 25% per tail with at least five
names per side, targets 80% gross, caps each symbol at 8%, and never exceeds 10% absolute net.

The first material evaluation is deliberately the no-control policy in `risk_policy.json`. No
parameter, risk control, or manual substitution may change after registration.

## Six-fold construction

The candidate is a fixed causal rule with no fitted coefficients. Each fold is nevertheless a
clean expanding-history replay and produces a separate immutable model/config artifact:

| Fold | Test interval (UTC, inclusive) | Training/history cutoff |
| --- | --- | --- |
| fold-1 | 2020-02-03 to 2020-08-31 | 2020-02-02 |
| fold-2 | 2020-09-01 to 2021-03-31 | 2020-08-31 |
| fold-3 | 2021-04-01 to 2021-10-31 | 2021-03-31 |
| fold-4 | 2021-11-01 to 2022-05-31 | 2021-10-31 |
| fold-5 | 2022-06-01 to 2022-12-31 | 2022-05-31 |
| fold-6 | 2023-01-01 to 2023-06-30 | 2022-12-31 |

Each worker may replay earlier authorized history for rolling state, but only its declared test
interval contributes to the stitched OOF series. There is no random CV and no cross-fold scaler.

## Falsifier and decision rule

Terminate the initial candidate without risk rescue if it is non-deterministic, invalid, insolvent,
or fails any causal truncation/source test. Reject the mechanism for this iteration if no-control
OOF net Sharpe is nonpositive, fewer than four folds have positive return, bull/bear/chop net return
is not positive, the long-bull or short-bear role is nonpositive, doubled-cost Sharpe is
nonpositive, or maximum drawdown exceeds 40%.

Only if that minimal mechanism screen passes may the preregistered one-axis neighborhood and risk
ablations run. Qualification still requires every stronger frozen tournament gate; passing this
screen is not qualification.

## Bounded allocation

- 1 initial no-control candidate.
- Up to 8 one-axis stability neighbors, only after the base mechanism screen.
- Up to 4 individual risk-control candidates and 1 combined control, only after positive base
  evidence.
- At most 14 material configurations for this family iteration, well inside the tournament-wide
  cumulative budget. Any rerun, failure, manual variant, or abandoned registered candidate counts.

Selection is gate-first: causal validity, deterministic replay, role/regime requirements, positive
doubled-cost Sharpe, and neighborhood stability. Among survivors only, prefer median fold Sharpe,
then lower drawdown, then lower turnover. Aggregate in-sample Sharpe alone never selects a model.
