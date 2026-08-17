# CUP-50

CUP-50 is an immutable tournament namespace. It does not import earlier candidate sources,
parameters, rankings, results, or conclusions. Only neutral protocol/execution code and
checksum-verified raw Binance archive bytes may be reused.

The complete machine policy is [`config.toml`](config.toml); the human policy is
[`TOURNAMENT-CHARTER-CUP50.md`](../../TOURNAMENT-CHARTER-CUP50.md). The lifecycle has one entrypoint:

```text
cup50 acquire | acquire-coverage | build | readiness | export-protocol |
      export-evaluator | activate | quarantine | trial | evaluate | nominate |
      field-close | observe | integrity-review | leaderboard | release | paper
```

Team research roots are generated outside this namespace and are accepted only after the
clean-room scanner proves that they contain no Git metadata, prior tournaments, private artifacts,
sealed data, reports, or untruncated caches. Evaluation runs in network-disabled, read-only Docker
containers with only protocol code and the sanitized team-visible IS snapshot mounted read-only.
That export has no transaction-open column, execution marks, or funding mark prices; organizer
execution uses a separately hashed IS snapshot that is never mounted into a team workspace.

No lane qualifies or is replaced. At field close each of the twelve lanes is either a source- and
neighbourhood-bound nomination or a DNF. Observation is one-shot and silent until the complete
leaderboard passes integrity review and is published atomically.

Acquisition is two-pass. `acquire` checksum-binds reusable caches and obtains the inclusive
terminal records for the preliminary exact-50 union. After `build`, `acquire-coverage` audits every
required execution boundary and uses checksummed monthly archives, then checksummed daily archives,
then exact public REST only where policy permits. A genuinely non-trading selected contract remains
in its frozen weekly roster and is never substituted. A pre-activation evidence audit makes it
non-executable from the first affected canonical boundary and force-settles a carried position at
the preceding verified transaction-bar close with ordinary costs. Any unaudited gap still fails
readiness. Coverage continues after roster exit wherever positive transaction activity remains. A
residual carried beyond roster exit is settled at the close of its last verified positive-activity
bar if the contract then stops trading. Hourly marks value every actual variable-frequency funding
settlement without substitution.
