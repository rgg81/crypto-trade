# Organizer static review — Team 05 initial CRTR draft

Disposition: **NO-GO for registration or execution; mechanism concept retained for remediation.**

## Sound elements

- The family is performance-blind, deterministic, two-sided, and economically falsifiable.
- Exposure is conservative and the fixed neighborhood is one-axis and nonselectable.
- The package records causal lineage, long/bull and short/bear roles, hard development gates, and
  explicit no-control/single-control/combined risk policies.
- No material trial or performance view has been consumed.

## Blocking corrections

1. `strategy.py` and its tests treat each bar frame's index as the timestamp. The real tournament
   worker supplies canonical bar columns, including `open_time`, on a non-time index. The strategy
   must consume that schema and admit a bar only after `open_time + 8h <= decision_time`.
2. Synthetic tests must use the real column schema. Their future-append/corrupt/truncate checks
   must distinguish bar open time from close availability.
3. The runtime seed should fail closed unless it equals the registered canonical seed `20260801`.
4. The prospective organizer score diagnostic requires the exact A5 identity hook at the
   post-transform/pre-selection boundary, a first-added candidate manifest, a complete simple
   executable-open-to-open label/IC contract, and byte-level invariance tests. Registration remains
   blocked until Amendment 0005 is frozen. *(Historical blocker at the time of this review; now
   resolved by the active authority rebind below.)*
5. The trial plan redundantly registers doubled-cost cells. The central evaluator already produces
   base and doubled-cost evidence for every risk policy in one material run. Collapse twelve
   risk/cost cells to six risk-policy cells.
6. Run the no-control core first. Risk controls may activate only after positive, broad core-alpha
   minima; they may not rescue a negative or one-regime mechanism. The fixed combined policy may be
   the canonical controlled candidate only after the core activation gate passes.
7. The top-level risk policy used by the initial trial must match that no-control sequence; preserve
   the combined policy as an immutable declared ablation until promotion.
8. The manually dated fold plan does not match the evaluator's six equal chronological slices.
   Bind exact evaluator-derived fold boundaries/model declarations before qualification evidence is
   recorded; do not claim retrained OOF evidence from incompatible dates.

After remediation, run lint, formatting, synthetic strategy tests, risk-contract tests, and each
policy validator serially. Do not register the family until every blocker is closed and all draft
hashes are recomputed.

## Team-05 remediation response

Status at remediation time: **all team-local corrections authored; registration remained blocked
on the external A5 freeze and all organizer verification/hash-binding steps.** No test, Python,
lifecycle, evaluator, or Git command was run during that remediation edit.

1. `strategy.py` now requires canonical RangeIndex frames with `open_time` and `close`, ignores the
   index as time, and admits only rows satisfying `open_time + 8h <= decision_time`.
2. Synthetic frames use that schema and distinguish an opened-but-unclosed row from the last
   exactly closed row; future append/corrupt/truncate checks include canonical score bytes.
3. Every runtime seed other than `20260801` is rejected.
4. The prospective direct v5 `score_boundary` call is post-transform/pre-selection and its return
   drives construction. The first-candidate manifest, executable-open-to-open label/IC contract,
   and byte tests are declared. The historical freeze blocker is superseded by the authority
   rebind below; artifact materialization and independent review remain pending.
5. `ablations.json` and `trial_plan.json` declare six policy runs, each with evaluator-produced base
   and doubled-cost evidence, followed by eight possible neighbors.
6. The sequence is no-control core, broad positive-alpha activation gate, single/combined controls,
   full combined-policy gates, then neighbors. Controls cannot rescue a failed core.
7. Top-level `risk_policy.json` is no-control; the immutable combined declaration is
   `risk_ablations/combined.json`.
8. Hand-dated fold declarations were removed. The plan consumes the organizer's exact equal
   chronological six-fold derivation before any fold evidence becomes admissible.

All earlier exact-looking draft hashes were removed or marked for recomputation.

## Active A5/A6 authority rebind

Disposition: **GO for fresh organizer QR/QE and prospective artifact materialization; NO-GO for
registration, execution, or any performance claim until the listed organizer steps finish.**

- Active entrypoint: `scripts/top40_v2_tournament_score_diagnostics_v5.py`, SHA-256
  `0dc9228f3b9c6fe41b2655055f766fc92f323a289a050e6bdf4e48a30b0105f4`.
- Active A5 integration freeze: commit `d2b95f610722aab65b4e67466b34efeaa3554101`, SHA-256
  `b3b2b96245a479ccfff95b5cd5b5cd0aef3b2d0aac0fc9faf5367d3e6772958c`.
- Delegated A6 integration freeze: commit `ed3af1398543dfee4a50150915dc2e37b3631fc9`, SHA-256
  `3e93bdfe031e2589888c3bbcaae583437bbd074fa9d86c6dc0a54187bc0f1e34`.
- A6 canonical pure-crypto report: 73,777 bytes, SHA-256
  `b9c55b40fef331861af068272159f45860870182a58c93652eff2a819b3d5d1b`, policy SHA-256
  `2c7fb0ff593d06c323517e60df4b28ab9387a2df580b83f82f65ef71c91fc350`, zero
  violations.

The normalized A5 templates now declare the exact active schema shapes and candidate-derived
paths. They deliberately retain invalid material placeholders. Before registration, the organizer
must freeze the final Team05 executable tree and materialize a sorted complete manifest containing
exactly every registered Team05 `.py` file, the staged `frozen_config.json`, and
`risk_policy.json`. The currently declared set is `candidate_variant.py`, `frozen_config.json`,
`risk_policy.json`, `strategy.py`, `test_risk_policy_contract.py`, and `test_strategy.py`; the
organizer must rederive the set from the actual historical tree rather than trust this prospective
list.

The canonical lifecycle always imports root `strategy.py` and reads root `risk_policy.json`.
`candidate_variant.py` is therefore a model-executable, hash-bound dependency: before every
material registration it must contain that predeclared candidate's exact ID, overrides, and
risk-template declaration. The selected `risk_ablations/*.json` declaration must likewise be copied byte-for-byte to root
`risk_policy.json` before the candidate commit. Declared side paths are never runtime selectors.

An independent reviewer must then inspect the exact manifest-bound strategy and all executable
dependencies, make the five fixed semantic findings, and first-add the candidate-specific review.
Only afterward may the score manifest bind that review SHA and the core registration bind the score
manifest SHA. A5 requires the executable-source commit to precede the semantic-review commit, which
precedes the score-manifest commit, which precedes the registration commit. Any executable-byte or
dependency-set drift restarts that sequence.

The A6 universe rule is inherited without exception: only certified native crypto coins/tokens are
eligible. Stablecoins, equities/TradFi, indexes, metals, commodities, and other non-crypto
contracts are excluded even when listed as Binance perpetuals. Team05 reads only the supplied
point-in-time eligible set and declares no local re-expansion.

No test, Python process, evaluator, lifecycle operation, or Git command was run for this authority
rebind. It records no semantic approval, registration, evaluation, or performance result.
