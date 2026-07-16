# Team 08 QE and static-review plan

Status: **planned; none of these checks has been executed by this draft**

## 1. Namespace and schema audit

1. Confirm all changes are confined to `teams/team-08` and both organizer projection ledgers retain
   their original bytes.
2. Validate every JSON document parses with duplicate-key rejection.
3. Replace both unmistakable timestamp placeholders with actual lifecycle timestamps, then validate
   `family_registration.draft.json` and the trial template against the exact frozen public schemas.
   Reject sentinel hashes at materialization even though they are syntactically schema-compatible.
4. Validate every full policy in `risk_ablations.json` and `risk_policy.json` through the public
   strict risk-policy parser.
5. Bind the active Amendment 0005 superset and require its delegated Amendment 0006 pure-crypto
   preflight for every later command.
6. Require root `risk_policy.json` to be byte-identical to `risk_policies/no-control.json` for the
   first material candidate. The lifecycle never selects `risk_policies/` directly.

## 2. Strategy static review

Review exact candidate bytes for forbidden I/O/imports, dynamic code loading, filesystem access,
environment or clock access, subprocess/network calls, hidden historical tables, prefitted
coefficients, mutable module state, stochastic ties, evaluator-state assumptions, and any attempt
to create fills or PnL. Confirm that all returned keys come from the current eligible set, all
weights are finite, requested gross is at most 0.80, requested absolute net is zero within numeric
tolerance, each symbol is at most 0.09, and both sleeves contain at least five symbols whenever the
book is non-flat.

Trace each transform in `feature_lineage.json` to code. In particular, confirm that the compression
window excludes the release bar, the dispersion baseline excludes the current bar, cross-sectional
residualization uses only the same closed boundary, uncompressed symbols are removed before score
centering or selection, and no future row is silently trimmed.

## 3. Team-side deterministic tests

Run `test_strategy.py` in isolation and review failures before any lifecycle action. Its required
coverage is:

- expansion produces material long and short sleeves;
- uncompressed names cannot re-enter through median centering or portfolio selection;
- low-dispersion failed releases reverse the direction of isolated dislocations;
- future, incomplete, corrupt, duplicate, unordered, and symbol-mismatched rows fail closed;
- insufficient or gapped history requests flat rather than inventing data;
- non-rebalance boundaries return `None` only after validating the full context;
- point-in-time membership changes cannot leave an ineligible target;
- input ordering and seed value do not change deterministic output; and
- fresh full-history and incrementally enlarged past-only contexts agree at the same boundary;
- all 17 strategy parameters have explicit family domains; and
- all eight neighbors materialize to valid, byte-distinct parameter objects inside those domains.

Run `test_risk_policy_contract.py` against the public risk module. Confirm graduated drawdown
scales, no-leverage volatility scaling, position and time-stop triggers, deterministic cooldown
blocking, same-boundary reentry prevention, and the turnover instruction.

## 4. Organizer integration checks

These checks belong to the organizer because team code cannot price or execute them:

1. Execute the source bundle in the networkless/read-only clean worker twice and require byte-
   identical targets and worker transcripts.
2. Corrupt one future row, append one future row, truncate at each boundary, reorder input symbols,
   and replay with a different allowed seed. The expected causal/deterministic behavior must match
   the unit contract.
3. Verify decisions use closed data and strategy requests fill only at the next open.
4. Verify weekly point-in-time membership, forced membership/delisting exits, participation sharing,
   actual funding signs and timestamps, and ordinary fee/slippage centrally.
5. Verify risk action order is funding, boundary valuation, risk evaluation, next-open reduction,
   strategy gate/request, common limits; risk reductions and strategy requests share capacity.
6. Verify a stopped or timed-out symbol cannot reopen at the same boundary and all actions pay
   ordinary costs.
7. Derive long/short attribution, turnover, risk-action counts, requested/filled risk notional, and
   base-versus-doubled-cost results only from canonical artifacts.

## 5. Research lifecycle checks

1. Replace the family draft timestamp and submit it through the active Amendment 0005 superset
   entrypoint before any material run; do not append `families.jsonl` manually.
2. Materialize actual source/config/risk hashes into a trial registration, validate exact schema,
   and register it before reading a result.
   The first risk hash must bind the no-control root bytes. Run this core first and require positive
   base- and doubled-cost return/Sharpe, at least four positive folds, positive bull/bear/chop
   returns, positive long-bull/short-bear/combined-chop attribution, and active sleeves before any
   control. Controls cannot rescue failure.
3. Run six declared chronological development folds. A fixed-rule fold artifact must bind its
   training cutoff, test interval, exact source/config hashes, and a no-learned-state declaration.
4. Store a stitched daily-return artifact derived only from fold test predictions. Fixed slices of
   one already scored backtest are not acceptable.
5. Register every mechanism, parameter, and risk variant before execution; interrupted and failed
   jobs remain counted.
6. Materialize at least three byte-distinct neighborhood parameter artifacts and their distinct
   daily-return series before invoking the stability gate.
7. Advance only if every frozen development gate passes. Never freeze a negative or gate-failing
   candidate as a submission.
8. For every later policy, copy its immutable `risk_policies/` template byte-for-byte to root
   `risk_policy.json` before commit, registration, and execution, then recompute all risk/source
   bindings.

## 6. Review disposition

The static reviewer returns `GO` only when exact bytes, public-schema compatibility, causality,
clean-process reproducibility, and all organizer integration checks pass. Any observed performance
is outside static review. A `GO` authorizes registration/evaluation, not qualification, private
access, or a performance claim.
