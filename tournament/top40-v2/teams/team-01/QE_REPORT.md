# Team 01 QE handoff: `rctc-pivot-ref-001`

Status: **pivot reference implemented; tests written but not run; not registered or evaluated**

## Implementation binding

The root `strategy.py` factory now returns `RegimeConditionalTrendCarryStrategy` with the exact
`PIVOT_REFERENCE_PARAMETERS`. State and direction use BTC's 60-day log return ending at `t-1d`:
bull at `>=+0.10`, bear at `<=-0.10`, chop otherwise. Exact missing state anchors request flat.

Bull/chop use the H14/K3/gamma0.5 path-efficient BTC-residual continuation transform. Bear uses the
same transform on raw asset returns, including raw sample volatility for sleeve sizing. Funding,
signed tails, inverse-volatility winsorization, capped-simplex construction, gross, caps, tilt,
coverage rules, runtime seed, and the disabled no-control policy remain frozen.

The stopped parent family and its post-result evidence remain untouched. This is a new family
package under `pivot-01/`, not another old-family coordinate.

## Declared contract coverage

The updated synthetic suite covers causal closed-row handling, future-data corruption invariance,
strict funding availability, membership removal, daily clock and seed behavior, deterministic
tie-breaking, exact residual versus raw branch formulas, state threshold/lag behavior, invalid-data
flat requests, target bounds, direct-versus-namespaced worker equality, and frozen-config/policy
binding.

No suite was run while preparing this package. Therefore the new target hash, file hashes, pass
count, duration, worker process evidence, dependency versions actually tested, and replay identity
remain pending in `test_evidence.json`. The old H14 hash and pass count are not reused.

## Organizer verification

Run the commands in `pivot-01/commands.json` sequentially. First run the local suite twice, record
the exact outputs and hashes, then replace all `PENDING_` fields. Only after those checks may the
organizer register the pivot family, register the exact no-control reference, and execute its single
development window.

Neighborhood, ablation, risk, private, and final commands are intentionally not authorized by this
handoff. They remain conditional on a fresh post-reference review applying the frozen causal and
role falsifier.
