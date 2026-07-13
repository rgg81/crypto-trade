# Clean-room provenance

I, the team-09 QR, independently proposed FPEG for this tournament on 2026-07-13. It was not selected from Git history, an old strategy/report/branch, portfolio code, another team namespace, or any public-OOS row. Public OOS was not accessed.

Bound records: Phase-0 `012727865acecad6ea0c3327745359820b8e45c6`; common freeze `48df09341f02eba7a3469abd1ccda6649a4ef0ba`.

## Materials consulted

I read only the supplied Top-40 charter, config, policy, manifest, methodology distillation, exact Top-40 QR agent definition, neutral `src/crypto_trade/tournament` modules, the team-09 namespace, and the complete local `feature-engineering`, `regime-detection`, and `walk-forward-validation` `SKILL.md` files. Their timestamp, past-only-state, and nested-validation controls shaped the specification; their example signals did not. I did not read another team, an old portfolio branch/artifact, an old trade idea, or any public-OOS output. No external research or vendor source was consulted.

## Strict cutoff and source audit

Every market scan was predicate-bounded before conversion to a pandas frame:

- `bars.open_time < 2024-07-01T00:00:00Z`: 680,320 rows; maximum `2024-06-30T16:00:00Z`;
- `funding.funding_time < cutoff`: 502,901 rows; maximum `2024-06-30T20:00:00.004Z`;
- `mark_prices.mark_time < cutoff`: 481,084 rows; maximum `2024-06-30T16:00:00Z`;
- `membership.reconstitution_time < cutoff`: 8,666 rows; maximum `2024-06-24T00:00:00Z`.

Only required columns were projected. Each resulting maximum was asserted strictly below the cutoff. The canonical full-window runner was deliberately not called because it would load public OOS. No timestamp at or after 2024-07-01 was loaded, even transiently, and public-OOS view count is zero.

Manifest-bound inputs are bars `f6f6364c34d23725d96a41c5cec216a83ca8cb05145e70b56aa239508b1cb99b`, funding `90f0e4702752cadc314b1aaac58175357dca14617c2a4243bdad51c366dbbeb9`, mark prices `8bf341f358cda3d2fa41f2a4d1290c1851114416f04b137386d0cf13e49ec4b0`, and membership `f51c9eb207c1da51cc4b9ff6045bb5e914828015b5c9c214f0e2673cd868eb14`. The manifest itself is SHA-256 `077eb036d262befec80f7013084fe6906859f7c3bbe2f8c193c9d9ec68e367c3`; config is `030a065f75f9c4adb7484065908f4379435929609d446be0de0a831d9e28ee0a`.

Neutral code bindings used for exact execution are engine `44c1fb93f2d434c845cfea367a3a9760997d947ecdf8b3be25c86a9112d40835`, metrics `abc32eca2752d7b04121554e04348310aec046c0676b3b7c743c4f909e4c7e2b`, and PIT data helper `de41fbcb6e007bff3059e266a2ec022d4e3ac9830bf480c28e0627d46c15c1ae`. The reference team target implementation replayed for the mechanical finalist is `07a5fabe781e44421faf3825c496568327fb1c3297794b1fe3a305f0fe621e7b`.

## Selection and evidence lineage

Before looking at performance I resolved the `D_t` ambiguity conservatively: nearest-rank thresholds are calculated from prior valid `D_s`, `s<t`, truncated to the most recent `L`; current `D_t` is appended only after today's gross is determined. This binding is `dispersion_history_includes_current=false` and was not treated as a second configuration.

The fixed 36-cell grid was proxy-screened with the frozen gate and tie order. Zero cells passed the final selector. The user-authorized mechanical fallback is `(q=.30,Gmax=.60,V=45d,L=180)`; its target mapping was then generated with the actual team strategy and executed through the neutral base/2x-cost engine. The reference target CSV serialization SHA-256 is `84fe97c9854cc407c2cba3aadb4b9dd138b53c273214fa8ce2b881c0bf189af2`. The canonicalized exact-finalist summary, hashed before adding its own hash field, is `37864beb7ea12802a114d0b0ebb78100788aca7d41cd106ef3be000125e1b8bc`. The analogous six-fold internal OOF summary hash is `f5e573a4792f563adce1a470feaaefb3ee27c47d95ab7c8b100172ed1cfc7dcb`.

The first vectorized preprocessing attempt exposed a pandas timestamp-unit mismatch (`datetime64[us]` versus Parquet nanoseconds), yielding zero valid cross-sections. It was stopped before any configuration was scored. A later empty-index dtype diagnostic also stopped before scoring. Both were implementation diagnostics, not hidden strategy trials; explicit nanosecond conversion and integer empty indices fixed them. No performance or parameter was observed before those fixes.

Successful timed stages were: complete 36-cell proxy/fold screen `12.09s wall / 15.77s CPU`; reference-target plus exact finalist/selector replay `936.17s wall / 937.84s CPU`; exact nested OOF plus proxy ablations `232.54s wall / 235.51s CPU`. Total successful compute was `1180.80s wall / 1189.12s CPU`, or about `0.3303 CPUh`, below the 12 CPU-hour and 18 wall-hour limits. The account contains 36 grid cells and six preregistered ablations = 42 material configurations, zero extra robustness configurations, and zero public-OOS views. Replaying a fixed configuration across folds and cost settings was not counted as a new configuration.

All negative findings are retained: the final selector gate fails, four later outer selectors require organizer fallback, aggregate internal OOF fails the acceptance gates, funding-only is within 0.10 Sharpe of joint in the proxy, and no-demean/equal-weight ablations outperform joint. The mechanical cell is advanced only because performance is not a charter DQ; it is explicitly not QR-accepted.

Signed: `team-09-QR / 2026-07-13 UTC`.
