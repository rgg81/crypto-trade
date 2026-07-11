# MN4 IDEA-05 — Kalman Stat-Arb on Major Pairs

**Pair:** QR+QE for IDEA-05 (Kalman Stat-Arb)
**Track:** MN4 blind tournament (10-idea parallel)
**Model:** Opus 4.8 (Fable rate-limited; user-directed). Disclosed per charter.
**Status:** FROZEN construction. IS-gate FAIL (negative Sharpe). NOT banked for reveal.

## 1. Hypothesis

Cointegrated major crypto pairs (BTC/ETH, SOL/BTC, top-10 majors) sustain
short-term mispricings that a Kalman-filtered hedge ratio + spread z-score
can capture at daily cadence. The structural-break kill-switch (rolling ADF
re-test) makes the construction regime-robust by exiting pairs when their
cointegration breaks — the canonical stat-arb failure mode.

This is the classical "Kalman stat-arb with adaptive hedge" — the kind of
strategy that has worked for decades in equities. The crypto-native question
is whether the edge (a) exists at daily cadence, (b) survives 5+2.5bps
two-leg cost, and (c) generalizes across regimes via the kill-switch.

## 2. Construction (FROZEN)

### 2.1 Universe

10 top-liquidity majors with full IS coverage (2020-01-01 onward):
BTC, ETH, BNB, XRP, ADA, LTC, BCH, LINK, TRX, ATOM.

C(10, 2) = 45 candidate pairs. No pre-screening — the rolling kill-switch
decides pair-by-pair which are tradeable at each rebal.

### 2.2 Kalman hedge + spread

State-space model per pair (A, B), log prices:
  x_t = [α_t, β_t]' (intercept + hedge ratio)
  y_t = log P_A[t] = H_t x_t + v_t , H_t = [1, log P_B[t]]
  x_t = x_{t-1} + w_t  (random walk — adaptive hedge)

Principle-anchored constants (round numbers, NOT fitted to IS outcomes):
  R_OBS   = 1e-3   (observation noise variance; chosen as the boundary where
                    the posterior spread has a tradable ~1-day half-life at 8h
                    cadence — calibrated on the canonical BTC/ETH pair)
  Q_α     = 1e-5   (intercept state-noise; slow)
  Q_β     = 1e-4   (hedge ratio state-noise; adaptive)

Calibration rationale: a grid-search on BTC/ETH over R ∈ {1e-3, 1e-2, 1e-1, 1.0}
showed R=1e-3 produces a posterior spread with AR(1) phi ≈ 0.75 → half-life
≈ 1 day at 8h cadence. Smaller R over-smooths (spread → 0); larger R
shortens the half-life to <0.5d (noise). R=1e-3 is the boundary of
tradeability, NOT a Sharpe-optimized pick (see diary §6).

Spread[t] = log P_A[t] - α[t] - β[t] × log P_B[t]  (KF posterior residual,
fully computable at close[t]).

### 2.3 Z-score + signal

z[t] = spread[t] / σ_t   (σ_t = rolling std over Z_WINDOW=360 8h-candles = 120d)
signal[t] = -z[t]   (high → long the spread = long A leg, short β×B leg)

NO |z|-entry gate. rank_neutral's demeaning naturally de-weights middle-rank
pairs (small |z|) toward zero — the entry threshold is implicit in the cross-section.

### 2.4 Structural-break kill-switch (THE RESEARCH PRIMITIVE)

For each pair at each candle t:
  rolling_coint_pvalue[t] = ADF p-value on the OLS residuals of
                            log P_A on (const, log P_B) over the trailing
                            ADF_WINDOW=270 8h-candles (90d)

  kill_switch_alive[t] = (pvalue[t] ≤ 0.10)
  universe[t, p]       = kill_switch_alive[t] AND finite z[t]

The kill-switch IS the research: the known stat-arb failure mode is regime
breaks (cointegration collapse). When the rolling ADF cannot reject unit
root (p > 0.10), the pair is killed — exited at the next rebal.

### 2.5 Synthetic pair panel → engine

The engine is signal-agnostic and operates on a (T, C) panel of NAMES. Each
pair becomes a synthetic "name" whose price tracks the cumulative dollar PnL
of $1 gross-spread exposure:

  pair_logret[k] = (log P_A[k+1] - log P_A[k]
                    - β[k-1] × (log P_B[k+1] - log P_B[k]))
                   / (1 + |β[k-1]|)
  pair_price[0] = 1.0
  pair_price[k+1] = pair_price[k] × exp(pair_logret[k])

The β[k-1] LAG (entry-time hedge) is critical: the position decided at
close[k-1] is filled at open[k] and held to open[k+1]. Using β[k-1] (known
at close[k-1]) gives the honest tradeable dollar PnL of $1 gross spread.

$1 of pair-name turnover = $1 total leg-notional turnover (both legs sum to
$1 gross), so engine cost_side = 7.5bps correctly charges the round-trip.

### 2.6 Engine configuration

  CostModel(taker_fee_bps=5.0, slippage_bps=2.5, funding_enable=True)
  weighting = "rank_neutral"  (cross-sectional L/S over the live pair universe)
  gross = 1.0   rebal = 3   (every 3 8h candles = daily, per charter)
  weight_cap = 0.20  (no single pair > 20% of gross)
  min_members = 4    (skip degenerate rebals when too few pairs alive)
  gross_scalar_series = crisis throttle (below)

### 2.7 Layer-2 crisis throttle (per-construction)

BTC 30-day realized vol ratio = rv30 / median(rv30 over 365d):
  ratio ≤ 2.0 → scalar = 1.0   (normal — 97% of IS)
  2.0 < ratio ≤ 3.0 → scalar = 0.5  (stress — 2.6% of IS)
  ratio > 3.0 → scalar = 0.0   (flat — blue-chip-core de-risk — 1.0% of IS)

CTA-standard round-number thresholds; NOT fitted to IS.

## 3. IS-Only Evidence

The honest-engine IS backtest (2020-01-01 → 2024-06-30, 4929 8h-candles,
4865 post-warmup) produced:

| Metric | Value |
|---|---|
| **Sharpe (1× cost)** | **−2.91** |
| Sharpe (2× cost, ground-truth twin) | −4.82 |
| Ann return | −39.4% |
| MaxDD | **−90.2%** |
| Turnover (one-way, annualized) | 436× |
| Win rate | 44.7% |
| # pairs traded | 45/45 (kill-switch gates occupancy, not membership) |
| Avg active pairs / rebal | 18.6 |
| Avg spread half-life | 0.3 days |
| Kill-switch off fraction | 0.587 |
| β_BTC (rolling 270-candle, mean) | **−0.003** (neutral by construction) |
| β_BTC (max) | +0.06 |
| Funding drag total | −133 bps (income — funding differential favored the book) |
| Crisis flat / half / full candles | 51 / 126 / 4752 |

Per-year Sharpe (1× cost):

| Year | Sharpe |
|---|---|
| 2020 | −3.45 |
| 2021 | −2.43 |
| 2022 | −4.88 |
| 2023 | −3.53 |
| 2024 (H1) | −0.06 |

Beta buckets (book_mean / btc_mean — small denominators make these noisy;
the rolling β_BTC above is the proper measure):

| Bucket | n   | book_mean | btc_mean | ratio |
|---|---|---|---|---|
| CRASH | 681  | +0.0004 | −0.0032 | −0.13 |
| CHOP  | 3466 | −0.0005 | +0.0004 | −1.03 |
| MANIA | 692  | −0.0005 | +0.0037 | −0.12 |

## 4. Pre-Registered IS Gate

| Criterion | Threshold | Result | Pass |
|---|---|---|---|
| IS Sharpe (1× cost) | > 0.0 | −2.91 | **FAIL** |
| IS Sharpe (2× cost) | > 0.0 | −4.82 | **FAIL** |
| Cost coverage (gross edge > 7.5bps/trade) | required | −3.1bps/trade | **FAIL** |

The IS-gate FAILs on every criterion. The strategy is not viable.

## 5. Why It Failed — The Diagnostic Finding

The most important research output is the DIAGNOSTIC, not the Sharpe. Two
findings:

### 5.1 The Kalman state-aware spread reverts, but the tradeable PnL does NOT

The KF posterior spread shows strong apparent mean-reversion: corr(z[t],
Δspread[t→t+1]) ≈ −0.54 on BTC/ETH — exactly what a stat-arb wants. BUT
this reversion is largely an ARTIFACT of the KF's mechanical state updates.

When the KF state (α, β) absorbs each new observation, the POSTERIOR residual
shrinks mechanically — independent of whether the underlying prices mean-revert.
The spread's "reversion" is partly the KF re-fitting its own state, not
tradeable price reversion.

The tradeable PnL of holding $1 gross spread with entry β[k-1] frozen for
the holding period is:
  pair_logret[k] = (Δlog P_A - β[k-1] × Δlog P_B) / (1+|β[k-1]|)

This captures the actual price moves, NOT the KF state changes. Per-trade
edge at lag=1 (8h cadence) on real crypto majors, pooled across 45 pairs:
  **mean = −3.1 bps, Sharpe(8h-annualized) = −0.70**

The tradeable edge is NEGATIVE — the apparent reversion is not realizable.

### 5.2 Proof: lag-decay on state-aware Δspread

If the state-aware Δspread edge were a TRUE tradeable signal, it would
persist across decision lags. It does NOT — it decays to zero within 10
candles:

| Decision lag | Mean (bps) | Sharpe (8h) |
|---|---|---|
| 1 | +25.7 | +6.72 |
| 2 | +14.9 | +3.93 |
| 3 | +7.6 | +2.04 |
| 5 | +3.5 | +0.94 |
| 10 | +0.5 | +0.14 |
| 20 | +0.4 | +0.12 |

This is a 1-candle leak via the KF's state update — by lag=10 the edge is
statistically zero. The +6.7 Sharpe at lag=1 captures the KF's own next-step
fit, NOT a tradeable signal. Confirms §5.1.

### 5.3 Stable negative tradeable edge across KF R tunings

To rule out a calibration failure, the tradeable edge was measured on real
crypto majors across R ∈ {1e-3, 1e-2, 1e-1, 1.0, 10.0}:

| R | mean/trade (bps, lag=1) | Sharpe |
|---|---|---|
| 1e-3 | −4.3 | −1.15 |
| 1e-2 | −3.5 | −0.94 |
| 1e-1 | −3.1 | −0.81 |
| 1.0 | −2.0 | −0.49 |
| 10.0 | −1.4 | −0.32 |

**No R value produces a positive tradeable edge.** The KF is correctly
calibrated; the underlying signal is just negative on real crypto majors at
daily cadence.

### 5.4 Sanity check on synthetic cointegrated data

To verify the pipeline WORKS when cointegration truly exists, the same
code was run on synthetic AR(1) cointegrated pairs (β=0.7, phi=0.7). The
KF recovers the true β within 0.03 (post-warmup median 0.74), and the
lagged_beta tradeable edge is **positive at lag=1** (Sharpe ≈ 0.13). The
construction correctly extracts mean reversion WHEN IT EXISTS — the real-
crypto null is a property of the data, not a pipeline bug.

## 6. Why It Failed — Cost + Structural

### 6.1 The spread mean-reverts at sub-daily cadence, not daily

The BTC/ETH spread's posterior AR(1) phi ≈ −0.75 at 8h (over-corrective),
implying a half-life < 1 day. By the time the daily rebal (rebal=3 on 8h
grid) fires, the reversion has already happened. The "residual" at daily
cadence is essentially momentum (slight positive autocorrelation).

The charter mandates daily frequency. Sub-daily reversion + daily execution
is a fundamental mismatch.

### 6.2 Cost is the binding constraint

436× annualized turnover × 7.5bps one-way = 32.7% annual cost drag. Even
if the per-trade edge were 0, this alone would drive Sharpe deeply negative.

The high turnover is structural: rank_neutral re-ranks every rebal. With
18 active pairs whose z-scores fluctuate by O(1) std between rebals, ranks
flip and positions turn over. The kill-switch + min_members + weight_cap
mitigate but don't eliminate this.

### 6.3 The 4-prior-track NULL pattern repeats

The MN1/MN2/MN3 prior tracks all concluded NULL on cross-sectional crypto
mechanisms at 8h-1h cadence. IDEA-05 confirms the pattern extends to
PAIRWISE cointegration-based stat-arb at daily cadence. Crypto majors are
not usefully cointegrated at the timescales compatible with cost-realistic
execution.

## 7. Risk Mitigation (pre-registered)

The construction includes the standard MN4 risk stack:
- Layer-2 crisis throttle (BTC 30d/365d vol ratio; pre-registered above)
- Kill-switch per pair (rolling ADF; structural-break exit)
- weight_cap = 0.20 (per-pair concentration cap)
- min_members = 4 (degenerate-rebal guard)

These all WORK as designed. The crisis throttle correctly fired during
stress periods (51 flat + 126 half-stress candles out of 4929). The kill-
switch correctly drops pairs during regime breaks (58.7% off-fraction).

## 8. Files (all in `analysis/portfolio/`, `tests/`, `data/mn4_idea05/`)

- `mn4_idea05_kalman.py` — KF + rolling z + rolling ADF (frozen, tested)
- `mn4_idea05_run.py` — full IS engine backtest runner (frozen)
- `mn4_idea05_leaks.py` — leak battery (5 tests, all pass)
- `tests/test_mn4_idea05_kalman.py` — 8 unit tests (causality + sanity)
- `tests/test_mn4_idea05_leaks.py` — pytest wrapper for leak battery
- `data/mn4_idea05/pair_features.npz` — cached per-pair KF outputs
- `data/mn4_idea05/is_results.json` — frozen IS scorecard

## 9. IS-Gate Verdict

**IS-Gate: FAIL. NOT banked for reveal.**

The construction is honest, leak-safe, and correctly implemented. The null
result is a property of the underlying data (crypto majors are not usefully
cointegrated at daily cadence), not a pipeline bug — verified by sanity
checks on synthetic cointegrated data. Per the charter's HONEST PRIOR, most
of the 10 ideas will fail; this is one of them, and the diagnostic finding
(§5.1-5.2) is a contribution to the dead-paths record.

The construction is FROZEN byte-exact; the IS scorecard is the one above.
If revealed on the holdout, the expected outcome is null — the strategy has
no positive edge to generalize.

## 10. What I Would Try Next (out of scope for this iteration)

If mandated to continue this axis:
- **8h-native cadence** (rebal=1) — captures the sub-daily reversion but
  violates the charter's daily mandate and likely still dies on cost.
- **Continuous re-hedging with explicit cost** — model the actual re-hedging
  turnover from β drift; may make the state-aware edge net-positive after
  honest re-hedging cost.
- **Funding-carry pairs** instead of price-cointegration — pick pairs where
  the funding-rate differential is mean-reverting (the carry trade). The
  BIS WP 1087 (2025) finding (10% carry shock → 22% liquidation jump)
  suggests a funding-based stat-arb may work where price-cointegration
  doesn't.
- **Cross-section beta-residual stat-arb** — instead of pairwise
  cointegration, fit a BTC+ETH factor model and trade the residuals. This
  is the canonical "stat-arb after factor removal" approach.

None of these are in scope for IDEA-05's seed (Kalman pairwise stat-arb on
major pairs). They are noted for the Critic's tournament review.
