# Team 08 research brief — volatility-dispersion release

Status: **prospective draft; not registered, not run, and not performance evidence**

## Family and mechanism

Family ID: `volatility-dispersion-release-v1`

The family targets a specific interaction rather than unconditional price momentum. A native
crypto contract first has to exhibit idiosyncratic volatility compression: its recent residual
volatility must be low relative to its own slower residual-volatility baseline. A newly closed bar
then supplies a possible release impulse. Cross-sectional residual dispersion decides whether that
impulse is treated as a genuine expansion or as a failed release:

- when cross-sectional dispersion expands materially, compressed assets with positive releases
  enter the long sleeve and those with negative releases enter the short sleeve;
- when dispersion remains subdued, the portfolio fades small release attempts because an isolated
  move without broad participation is more likely to converge; and
- between those states, the two scores blend continuously, avoiding a brittle regime switch.

Compression is a hard eligibility mask. A symbol whose fast-to-slow residual-volatility ratio is
at or above the declared ceiling is removed before score centering, ranking, or sleeve selection;
it cannot become tradable merely because active scores shift the cross-sectional median.

All symbol returns are residualized by the same-boundary cross-sectional median before volatility,
compression, release, and dispersion are computed. The strategy therefore seeks relative crypto
price discovery, not a disguised BTC-direction bet. The portfolio is rebuilt once daily at 00:00
UTC from bars already closed by that boundary and fills, if any, belong to the organizer at the
next open.

## Economic thesis

Crypto liquidity and attention arrive unevenly across contracts. A period of low asset-specific
variation can reflect temporarily balanced inventories. When a new imbalance appears across many
names at once, rising dispersion is evidence that information is being incorporated unevenly and
the release can persist. When the same asset-level displacement occurs without broad dispersion,
it is more plausibly a local liquidity disturbance or failed breakout and is faded. Conditioning
direction on both the pre-existing compression and the contemporaneous dispersion state is the
mechanism; a simple trailing-return sort is deliberately absent.

This thesis is falsified if compression-conditioned releases do not outperform their explicit
no-compression ablation, if the dispersion switch does not separate continuation from convergence,
or if the stitched chronological evidence is not positive across at least four folds and bull,
bear, and chop net returns are not all positive. Clearing an aggregate Sharpe while failing any
frozen development gate is also a falsification for tournament purposes.

## Expected regime and sleeve roles

- **Bull:** broad upside releases should put the strongest idiosyncratic expansions in the long
  sleeve. The short sleeve remains a relative-weakness hedge rather than a market short.
- **Bear:** downside releases should make the short sleeve the primary contributor; residualization
  prevents a uniform market fall from mechanically shorting every asset.
- **Chop:** low-dispersion failed releases activate the convergence mode on both sides. The combined
  portfolio, not either sleeve in isolation, is expected to carry this regime.
- **Stress:** dispersion expansion can recognize genuine breaks, while organizer-owned volatility
  targeting, stops, and drawdown brakes reduce exposure. Flat or modest behavior is acceptable;
  uncontrolled tail loss is not.
- **Long sleeve:** owns the strongest positive continuation scores in expansion and the weakest
  negative dislocations in convergence.
- **Short sleeve:** owns the strongest negative continuation scores in expansion and the weakest
  positive dislocations in convergence.

The default portfolio targets 0.80 gross, split equally between the sleeves, with at least five
positions per side and a 0.09 symbol cap. This makes both sleeves material while remaining below
the common 0.10 symbol limit and at zero requested net exposure before evaluator actions.

## Causal construction

At decision time `t`, every accepted bar satisfies `open_time + 8h <= t`; the most recent bar used
for a signal satisfies equality. Future or incomplete bars, naive timestamps, duplicate or
unordered times, symbol/key mismatches, non-finite prices, negative volume, non-past funding, or
unexpected auxiliary inputs cause a hard error. A symbol with too little contiguous history is
omitted. If fewer than twelve symbols remain, or if either sleeve lacks five qualifying names, the
strategy requests a flat book.

The Amendment 0006 pure-crypto preflight is the universe authority. Team code intentionally does
not guess asset class from ticker substrings; the active Amendment 0005 superset delegates through
that wrapper before the context can be supplied. The strategy still validates exact uppercase
`*USDT` syntax and the point-in-time membership/key equality.

No parameter is learned from a whole evaluation window. The initial candidate is a deterministic
fixed rule. Chronological fold artifacts will bind the same rule plus each fold cutoff, and all
selection-touched trials will be counted before their results are read.

The arrays under `family_registration.draft.json.parameter_ranges` are exact discrete prospective
domains, not min/max shorthand. They cover all 17 `StrategyConfig` fields; fixed fields use
singleton domains, and every center and declared-neighbor value appears explicitly.

## Prospective selection rule

A candidate is eligible to advance only if centrally generated stitched OOF evidence passes every
development threshold in `config.toml`, including the base and doubled-cost metrics, all six-fold,
quarter, regime, sleeve, concentration, trial-adjustment, drawdown, and parameter-neighborhood
gates. Among passing candidates, select lexicographically by:

1. highest minimum of bull, bear, and chop net Sharpe;
2. highest doubled-cost net Sharpe;
3. lowest maximum drawdown; and
4. lower one-way turnover.

The lexicographic rule is declared before results to prevent an attractive aggregate statistic
from compensating for a weak market condition. If nothing passes, continue within budget, make a
documented mechanism pivot, or record DNF; never submit the least-bad model.

The first material trial is the unchanged core signal with the top-level no-control
`risk_policy.json`. Before any volatility, drawdown, position-stop, time-stop, turnover, or combined
policy may be registered, that core must have strictly positive return and Sharpe at both ordinary
and doubled costs, at least four positive folds, positive bull/bear/chop returns, positive
long-bull, short-bear, and combined-chop attribution, and active long and short sleeves. Controls
cannot rescue a negative or otherwise failed core. Failure permits only a separately preregistered
mechanism revision/pivot or DNF, whose own no-control core must restart the sequence.

## Trial allocation

The prospective initial-family allocation is capped at 21 material configurations:

- one default candidate using the no-control root policy;
- eight single-axis/local parameter neighbors;
- five mechanism ablations;
- six additional risk-policy configurations (five individual controls plus combined), each at
  base and doubled cost inside its registered run; and
- one reserved confirmation rerun, used only after a candidate passes all visible gates.

`risk_ablations.json` contains seven policies because it also repeats the no-control policy for a
complete comparison matrix. That no-control policy is byte-identical to the default candidate's
root policy and is not counted a second time: `1 + 8 + 5 + 6 + 1 = 21`.

Every configuration is registered before execution. The empty organizer-owned ledgers remain
untouched by this draft. A failed or interrupted run still consumes its trial and resource budget.

## Risk hypothesis

The core initially has no risk overlay. Only after its broad positive activation gate passes may
the combined risk policy be materialized at root. It targets 35% annualized portfolio volatility
without leverage, applies
graduated brakes at 10%, 18%, and 26% drawdown, closes a position after a 7.5% boundary-confirmed
loss, times out holdings after 18 bars, and caps one-way turnover at 0.45. Stops and timeouts carry
cooldowns and cannot reopen on the same boundary. These controls are hypotheses, not assumed
improvements. `risk_ablations.json` declares no-control, each individual control, and combined
policies; every activated policy must be copied from its immutable template to root
`risk_policy.json` before commit, registration, and run, and must be measured at ordinary and
doubled costs. The lifecycle never selects a side-path template.

## Advance, revise, or stop

- **Advance:** all frozen development gates pass and at least 70% of declared local neighbors are
  profitable with median Sharpe at least 0.50.
- **Revise inside family:** the mechanism ablations support the thesis but a declared local axis or
  one risk control is clearly responsible for a non-tail gate failure.
- **Pivot:** the compression or dispersion-switch ablation falsifies the proposed interaction in a
  majority of folds.
- **DNF:** no family clears the gate within the cumulative budget, or any causal/reproducibility
  boundary cannot be demonstrated.

A control is never a valid **Revise** action for a failed no-control core. Any such revision is a new
mechanism candidate and must begin with a separately registered no-control trial.
