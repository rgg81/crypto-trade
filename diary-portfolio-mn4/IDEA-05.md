# MN4 IDEA-05 — Diary

**Decision: NO-MERGE / IS-GATE FAIL / NOT BANKED FOR REVEAL**

The Kalman stat-arb on major crypto pairs, run honestly through the engine
at daily cadence, has negative tradeable edge after cost. This is a clean
NULL result with an important diagnostic finding.

## What Worked

- The construction is leak-safe end-to-end (13 unit tests + 5 leak-battery
  tests pass). KF causality, rolling-z causality, rolling-ADF causality,
  append-invariance all verified by corrupt-future positive controls.
- The KF recovers the true hedge ratio on synthetic cointegrated data
  (β=0.74 vs true 0.7 within 0.03 post-warmup).
- The kill-switch correctly drops pairs during regime breaks (58.7% off-
  fraction — sensible given crypto's choppy cointegration).
- The crisis throttle correctly fires during stress periods (177 of 4929
  candles in flat/half-stress).
- The book IS market-neutral by construction: rolling β_BTC mean = −0.003,
  max = +0.06.
- The honest-engine IS scorecard is reproducible (cached features +
  deterministic KF).

## What Failed

### 1. The KF state-aware spread APPEARS to revert but the tradeable PnL does not

This is the most important finding. The KF posterior spread on BTC/ETH
shows strong apparent mean-reversion: corr(z[t], Δspread[t→t+1]) ≈ −0.54.
At face value, this is a stat-arb's dream signal.

But the tradeable PnL (the per-candle dollar return of $1 gross spread
held with entry β[k-1] frozen) is **negative**: −3.1 bps per trade pooled
across 45 major pairs at lag=1 (8h cadence).

The mismatch: the KF state (α, β) updates each step to fit the latest
observation. The POSTERIOR residual mechanically shrinks — this is the KF
"explaining away" the mispricing, not the underlying price reverting. The
spread's apparent reversion is partly an artifact of the KF's own state
adaptation, not a tradeable signal.

### 2. Proof: the state-aware edge is a 1-candle leak artifact

If Δspread (state-aware) were a true tradeable signal, it would persist
across decision lags. It does NOT — it decays to zero within 10 candles:

| Lag | Mean (bps) | Sharpe (8h) |
|---|---|---|
| 1 | +25.7 | +6.72 |
| 5 | +3.5 | +0.94 |
| 10 | +0.5 | +0.14 |
| 20 | +0.4 | +0.12 |

The +6.7 Sharpe at lag=1 is the KF's mechanical next-step fit. By lag=10
it is statistically zero. The HONEST lagged_beta construction (entry β
frozen for the hold) shows stable −1 to −3 bps across lags 1-20 (no leak,
just no edge).

### 3. No KF calibration produces a positive edge on real crypto

To rule out miscalibration, the tradeable edge was measured on real crypto
majors across R ∈ {1e-3, 1e-2, 1e-1, 1.0, 10.0}. **None produce a positive
tradeable edge.** The KF is correctly calibrated; the signal just isn't
there.

### 4. The pipeline works on synthetic cointegrated data

Same code, synthetic AR(1) cointegrated pair (β=0.7, phi=0.7): KF recovers
true β, lagged_beta edge is positive at lag=1 (Sharpe ≈ 0.13). The
construction correctly extracts mean reversion WHEN IT EXISTS. The real-
crypto NULL is a property of the data, not the pipeline.

### 5. Cost amplifies the underlying anti-edge

Even at 0 per-trade edge, the 436× annualized turnover would drive Sharpe
deeply negative. The structural issue: rank_neutral re-ranks every rebal
with 18 active pairs whose z-scores shift by O(1) std between rebals →
positions turn over. The kill-switch + min_members + weight_cap mitigate
but cannot eliminate this.

## Headline IS Scorecard (FROZEN)

```
Sharpe 1× cost:  −2.91        Sharpe 2× cost:  −4.82
MaxDD:           −90.2%       Ann return:      −39.4%
Turnover:        436× annualized
Win rate:        44.7%
# pairs:         45/45 (kill-switch gates occupancy)
Avg active/rebal: 18.6
Avg half-life:   0.3 days
Kill-switch off: 58.7%
β_BTC mean:      −0.003       β_BTC max:       +0.06
Funding drag:    −133 bps (income)
Crisis throttle: 51 flat / 126 half / 4752 full
```

Per-year Sharpe: 2020: −3.45, 2021: −2.43, 2022: −4.88, 2023: −3.53, 2024-H1: −0.06.
All years negative; the book never finds a positive regime.

## Lessons

### Lesson 1: The Kalman state-aware spread IC overstates tradeability

The standard Kalman stat-arb literature reports the IC of z vs Δspread as
evidence of mean reversion. This is **methodologically incomplete**: the
state-aware Δspread includes the KF's own state adaptation, which is
non-tradeable. The honest metric is the lagged_beta pair_logret, which
captures only the actual price moves at entry β. On real crypto majors,
the IC measured this way is +0.05 pooled (essentially zero) and the
realized edge is negative.

**Action for future stat-arb work**: always validate IC against the
TRADEABLE return (entry-β-frozen pair_logret), not the state-aware Δspread.
The state-aware IC is a necessary-but-not-sufficient sanity check.

### Lesson 2: Crypto majors are not usefully cointegrated at daily cadence

The 4-prior-track NULL pattern (MN1/MN2/MN3 + IDEA-05) extends to pairwise
cointegration. Crypto majors share the BTC factor strongly but are not
pairwise mean-reverting at the timescales compatible with cost-realistic
daily execution. Sub-daily reversion (half-life < 1 day) is real but
requires sub-daily execution, which conflicts with the charter's "slow-
favored daily" mandate and would likely die on cost regardless.

### Lesson 3: Kill-switch design worked exactly as intended

The structural-break kill-switch (rolling ADF, p ≤ 0.10) is the one piece
of the construction that performed exactly as designed. It correctly
identified regime breaks (58.7% off-fraction — sensible given crypto's
broken cointegration regimes) and would be reusable in any future stat-arb
work on more cointegrated assets (equities, commodities).

### Lesson 4: Apparent IC ≠ tradeable edge — a general lesson

The +0.54 IC of z vs −Δspread on BTC/ETH looked like a strong signal. The
tradeable edge was −3 bps. This gap (between correlation-implied edge and
realized tradeable edge) is a general methodological trap, not unique to
crypto or Kalman stat-arb. The lesson generalizes: ALWAYS decompose the
signal-return relationship into (i) what the signal predicts, (ii) what
the position actually earns. They are not always the same thing.

## Cost Coverage Analysis

Per-trade gross edge (cost-ignorant, lag=1): **−3.1 bps**
Per-trade cost (one-way, two legs): 7.5 bps
Per-trade net: **−10.6 bps**

Even at zero cost, the strategy has no edge. Cost is the second problem,
not the first. The first problem is the underlying signal is anti-
predictive at the daily cadence.

## Multiple-Testing Awareness

This construction is ONE of TEN in the MN4 tournament. The IS-gate FAIL
is reported with full honesty. Per the charter's HONEST PRIOR, most of the
10 will fail; the diagnostic finding (state-aware spread IC overstates
tradeability) is a contribution to the dead-paths record that protects
future stat-arb work in this track from repeating the same methodological
trap.

## Model Disclosure

Opus 4.8 (Claude). Fable was rate-limited this session; the user directed
a switch to Opus. Disclosed per charter §"Model".

## What I Would Try Next (NOT in scope for IDEA-05)

For the Critic's tournament review or any future continuation:

1. **Funding-carry stat-arb**: trade the funding-rate differential, not
   the price cointegration. BIS WP 1087 (2025) shows the funding-rate
   mechanism is sharper than price reversion for crypto.
2. **Cross-section factor-residual stat-arb**: fit a BTC+ETH factor model,
   trade the residuals. Removes the dominant factor before testing for
   pairwise mean reversion.
3. **Continuous re-hedging with honest cost**: explicitly model the re-
   hedging turnover from β drift. May reveal that the state-aware edge is
   net-positive after honest continuous-rehedging cost.
4. **8h-native cadence**: violates the charter's daily mandate but is the
   natural frequency for crypto perp funding cycles. The charter's daily
   constraint may itself be a mismatch for Kalman stat-arb on crypto.

None of these are within the IDEA-05 seed (Kalman pairwise stat-arb on
major pairs at daily cadence). They are flagged for the Critic.

## Files

- `briefs-portfolio-mn4/IDEA-05.md` — the brief (research design + IS scorecard)
- `analysis/portfolio/mn4_idea05_kalman.py` — KF + z + ADF (frozen)
- `analysis/portfolio/mn4_idea05_run.py` — engine backtest runner (frozen)
- `analysis/portfolio/mn4_idea05_leaks.py` — leak battery
- `tests/test_mn4_idea05_kalman.py` — 8 unit tests
- `tests/test_mn4_idea05_leaks.py` — pytest leak wrapper
- `data/mn4_idea05/pair_features.npz` — cached KF outputs
- `data/mn4_idea05/is_results.json` — frozen IS scorecard JSON

## Final Verdict

IS-Gate FAIL. NOT banked for reveal. The construction is honest, frozen,
and the negative result is a real finding (crypto majors are not cost-
surviving cointegrated at daily cadence; the apparent KF edge is a state-
update artifact). This is the methodology working as designed.
