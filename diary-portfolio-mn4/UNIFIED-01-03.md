# MN4 UNIFIED-01-03 — single-signal merge of IDEA-01 (TS-mom) + IDEA-03 (regime-adaptive)

**User-directed 2026-07-12.** The prior mn4_ensemble_0103.py was a RETURNS-LEVEL
blend (two frozen sub-books' daily returns mixed at the inverse-vol weight). The
user's mandate: "build a live component that can reproduce the backtest bit by
bit, and they need to generate one signal." This module IS that single signal —
a SIGNAL-LEVEL merge that drives ONE blind_engine.run_backtest call, produces
ONE returns stream, and is bit-by-bit reproducible by a live component that only
ever sees `panel[:k+1]` at decision time `k`.

**Model note:** Engineered on Opus 4.8 (Claude Fable rate-limited; user-directed).

## The merge (one composite signal, one engine call, one P&L)

The two members' raw alpha arrays are rank-normalized per candle (comparable
scale), blended with the inverse-vol weight from the ensemble, and the single
composite signal drives the engine. Recipe (every constant frozen):

- **Composite signal:** `sig_merge[t,c] = α·rn(sig01)[t,c] + (1-α)·rn(sig03)[t,c]`
  where `rn()` is per-candle cross-sectional rank over each member's OWN universe
  (centered fraction in [-0.5, +0.5]). Names missing from one member's universe
  get rank 0 (neutral) on that leg. **α = 0.5887** (IDEA-01 inverse-vol weight
  from mn4_ensemble_0103 — member-statistics-only, no IS-Sharpe fit; the capstone
  anti-mining rule).
- **Composite universe:** `univ01 | univ03` (union — broad top-20 ∪ blue-chip core).
- **Composite gross_scalar:** `min(scalar01, scalar03)` per candle — the MORE
  CONSERVATIVE de-risk. Flat in CRISIS via 03's 0.0, halved in STRESS or CRASH.
  Keeps the strongest crisis defense of either model.
- **One `run_backtest`:** `weighting="rank_neutral"`, `gross=1.0`,
  HedgeOverlay BTC + conditional ETH leg (03's stronger neutrality primitive;
  both members are market-neutral), `vol_target_ann=0.30` + `max_lev=1.5`,
  `dd_brake (0.15/0.50/0.075)`, `rebal=3` (DAILY — required so 03's CRISIS_DWELL=3
  catches every crisis; 01's slow 4w signal changes little day-to-day so daily
  re-rank is low-turnover), `CostModel(5, 2.5, funding=True)`, 2×-GT twin `(10, 5)`.

## Scorecard (8h-domain, the engine's native cadence — authoritative)

| Metric | IS [2020-01-01, 2024-07-01) | HOLDOUT [2024-07-01, 2026-07-01) |
|---|---|---|
| **n_periods (8h candles)** | 4658 | 2189 |
| **Sharpe 1×** | **+1.804** | **+1.171** |
| **Sharpe 2×-GT** | **+1.461** | **+0.951** |
| t_stat (1×) | +3.72 | +1.66 |
| Ann return | +59.4% | +45.5% |
| Ann vol | 28.0% | 37.9% |
| maxDD | −28.8% | **−25.0%** (improved vs IS!) |
| Win rate | 0.494 | 0.507 |
| Turnover (1-way, ann) | 123× | 120× |
| Mean gross leverage | 0.822 | 0.794 |
| Final equity | 7.32 | 2.12 |

**Sharpe 2×/1× = 0.81 IS, 0.81 holdout** — robust to 2× cost in both windows.

### Per-year Sharpe (1×)

| Year | IS | HOLDOUT |
|---|---|---|
| 2020 | +3.99 | — |
| 2021 | +2.94 | — |
| 2022 | +0.11 | — |
| 2023 | +1.00 | — |
| 2024 | +0.43 (H1 only) | +0.94 (H2) |
| 2025 | — | +1.38 |
| 2026 | — | +0.92 (H1) |

### Per-half Sharpe (1×)

| Half | IS | HOLDOUT |
|---|---|---|
| H1 (Jan-Jun) | +1.26 | +1.45 |
| H2 (Jul-Dec) | +2.32 | +0.84 |

All four holdout halves positive (H1+H2 across both 2024-25 and 2025-26). The
soft H2-holdout (+0.84) is the adverse 2025-H2 environment the ensemble diary
called out; the unified book holds positive through it.

### Regime-bucket attribution

| Bucket | IS n | IS Sharpe | IS cum | HO n | HO Sharpe | HO cum |
|---|---|---|---|---|---|---|
| CRASH | 570 | −0.39 | −4.9% | 269 | −0.24 | −1.8% |
| MANIA | 890 | +2.18 | +72.1% | 109 | +4.01 | +10.4% |
| CHOP | 3198 | +1.98 | +343.6% | 1811 | +1.20 | +95.2% |

CRASH is approximately flat (slight bleed within the de-risk envelope, |cum| <5%
IS and <2% holdout — the conservative `min(scalar01, scalar03)` works as
designed). Edge concentrates in MANIA + CHOP — the same regime profile the
parents exhibited, now combined.

### Market neutrality (rolling-270c β + regime-bucket β)

| β metric | IS | HOLDOUT |
|---|---|---|
| β_BTC rolling-270c mean | +0.017 | +0.004 |
| β_BTC rolling-270c |p95| | 0.141 | 0.112 |
| β_ETH rolling-270c mean | +0.011 | −0.002 |
| β_BTC \| CRASH bucket | +0.009 | −0.059 |
| β_BTC \| MANIA bucket | +0.024 | n/a* |
| β_ETH \| CRASH bucket | +0.014 | n/a* |
| β_ETH \| MANIA bucket | −0.005 | n/a* |

The hedge overlay delivers the market-neutral mandate: rolling β_BTC mean ≈ 0,
|p95| < 0.15 both windows. The CRASH-bucket β on holdout (−0.059) is small
absolute but worth flagging — the de-risked book holds a slight short tilt into
crashes (a known signature of TS-mom books that go long up-trends and short
down-trends; the conservative scalar flattens most of it).

### Composite gross_scalar occupancy

| State | IS | HOLDOUT |
|---|---|---|
| Flat (CRISIS, scalar=0.0) | 0.8% | 0.5% |
| Half-gross (STRESS or CRASH, scalar=0.5) | 28.6% | 16.0% |
| Full gross (NORMAL, scalar=1.0) | 70.6% | 83.4% |

The min-scalar rule engages the de-risk primitives a meaningful fraction of the
time (CRISIS+STRESS = ~30% IS, ~17% holdout) — these are the risk primitives
actually firing, not inert constants.

## The REPLAY / bit-by-bit reproducibility test — the core value

**This is the load-bearing deliverable.** A live component that only ever sees
`panel[:k+1]` at decision time `k` MUST reproduce the backtest's composite
decision bit-for-bit. The module ships:

- `composite_signal_at(panel, k)` — pure past-only; returns the (C,) composite
  signal vector at `k`, computed from `panel[:k+1]` only.
- `composite_universe_at(panel, k)` — likewise, for universe membership.
- `composite_scalar_at(panel, k)` — likewise, for the gross scalar.
- `composite_target_weights(panel, k, gross)` — likewise, for the alpha target
  weight vector (engine's rank_neutral builder applied to the composite signal).

**The replay test (run on the real IS panel):**

```
csig_full = composite_signal(panel)            # the (T,C) array the engine saw
for k in sample_of_candles:                     # 22 candles: every 500th + 12 consecutive rebals
    pt = panel[:k+1]                             # truncated to data known at close[k]
    csig_k = composite_signal_at(pt, k)         # the live component's view
    assert array_equal(csig_k, csig_full[k])    # BIT-IDENTICAL — no future leak
```

**Result on the IS panel: PASS — bit-by-bit confirmed.**
- Composite signal: 22/22 bit-identical
- Composite universe: 22/22 bit-identical
- Composite scalar: 22/22 bit-identical
- `composite_target_weights` spot-check: 5/5 rebal candles bit-identical
  (n_held=10, sum|w|=1.0000 at each)

The comprehensive every-50th-candle + every-rebal-candle replay is the unit
test (`tests/test_mn4_unified_0103.py::test_replay_*` — 5 tests, all pass on
synthetic data). The property holds because every member primitive
(`tsmom_signal`, `composite_signal_03`, `regime_conditional_universe`,
`crisis_scalar`, `detect_regime`) is itself bit-identical on truncation — the
composite inherits the past-only property, and the rank-normalize + blend +
min-scalar are per-candle pure functions of those.

### Leak battery (on the composite primitives)

| Check | Result |
|---|---|
| corrupt-future composite_signal[:t0] bit-identical | PASS |
| corrupt-future composite_universe[:t0] bit-identical | PASS |
| corrupt-future composite_scalar[:t0] bit-identical | PASS |
| decision-lag [k-1] equity[:t0+1] bit-identical | PASS |

## Honest comparison to the alternatives

| Construction | IS Sharpe (1×) | HO Sharpe (1×) | HO Sharpe (2×-GT) | HO maxDD | Notes |
|---|---|---|---|---|---|
| IDEA-01 alone (TS-mom) | +0.92 | +1.11 | +0.97 | −26.3% | weekly rebal, β-hedged |
| IDEA-03 alone (regime-adaptive) | +1.56 | +1.08 | n/a | −39.1% | daily rebal, regime de-risk |
| Prior ensemble (returns-blend) | +1.47 | +1.28 | n/a | **−18.2%** | two sub-books, returns-level |
| **UNIFIED-01-03 (this module)** | **+1.80** | **+1.17** | **+0.95** | **−25.0%** | ONE signal, ONE engine call |

**Reads:**
- **vs each parent:** The unified book Sharpe-beats both members on IS (+1.80 >
  +0.92, +1.56) and matches/exceeds on holdout (+1.17 vs +1.11, +1.08). The
  merge ISN'T just averaging — it's ranking-and-blending per candle, which
  captures the cross-sectional agreement between the two alpha arrays.
- **vs the returns-blend ensemble (+1.28 holdout):** The unified book is
  slightly BELOW the ensemble on holdout Sharpe (+1.17 vs +1.28) and slightly
  worse on maxDD (−25% vs −18%). This is the honest cost of the single-signal
  constraint: the returns-blend diversifies across two independent sub-books
  with different rebal cadences (01 weekly + 03 daily), so it captures
  timing-diversification the unified book can't (the unified book must pick ONE
  cadence — daily, dictated by 03's CRISIS_DWELL=3). The trade is structural
  simplicity + TRUE single-signal tradability: one composite signal, one engine
  call, one P&L, bit-by-bit live parity. The ensemble's −18% maxDD came from a
  static 59/41 capital split between two independent books; the unified book
  CAN'T diversify that way because it's a single book by construction.
- **maxDD asymmetry:** Holdout maxDD (−25.0%) is BETTER than IS maxDD (−28.8%)
  — the unified book generalized favorably on the drawdown axis. The
  crisis-defense primitive (min-scalar) engaged less often in holdout (16% vs
  28.6% in STRESS/CRASH) — calmer holdout regime, partly.
- **Caveat (kept honest):** The holdout window is the same one both members
  were revealed on (MN4-01 + MN4-03 tokens spent). The unified book's holdout
  result is real but contaminated by the design discussion; the clean test is
  forward paper-trading on genuinely-unseen post-2026-06 data. Forward paper
  trade is the clean arbiter and the user's designated next step.

## Live-component wiring spec

At candle `k` (close just published), the live component:

1. **Load** `panel[:k+1]` (kline fetch through `close[k]`).
2. **Decide** the alpha target via the live entry point:
   ```python
   from mn4_unified_0103 import composite_target_weights, GROSS
   w_alpha = composite_target_weights(panel, k, GROSS)   # (C,) vector, past-only
   ```
3. **Hedge sizing** (BTC + conditional ETH leg, past-only):
   ```python
   from mn_beta import rolling_beta, rolling_residual_beta
   beta_btc = rolling_beta(panel, ref="BTCUSDT")            # (T,C) — row k
   beta_eth_resid = rolling_residual_beta(panel, ref="ETHUSDT", base="BTCUSDT")
   # apply the engine's _hedge_target_row sizing at row k (see blind_engine)
   ```
4. **If `(k+1) % rebal == 0`** (next candle is a rebal), execute `w_alpha + w_hedge`
   at `open[k+1]`.

The bit-by-bit replay test proves step 2 is a pure function of `panel[:k+1]` —
identical code path in backtest and live → bit-identical decisions. The hedge
sizing (step 3) and the engine's downstream vol-target / dd-brake are shared
code already unit-tested for past-only behavior.

The exact signatures (frozen; live component calls these):

```python
composite_signal_at(panel: Panel, k: int, *, alpha_01: float = 0.5887) -> np.ndarray
composite_universe_at(panel: Panel, k: int) -> np.ndarray
composite_scalar_at(panel: Panel, k: int) -> float
composite_target_weights(panel: Panel, k: int, gross: float, *, alpha_01: float = 0.5887) -> np.ndarray
```

All four take the panel (truncated or full — they only read `panel[:k+1]`) and
return the per-candle decision at `k`. Pass the growing panel as `panel` and
the current candle index as `k`; the return value is what to execute at the
next rebal step.

## Status / hand-off

- Module: `analysis/portfolio/mn4_unified_0103.py` — frozen, lint-clean.
- Tests: `tests/test_mn4_unified_0103.py` — 22 tests, all PASS (incl. the
  comprehensive replay on synthetic data + corrupt-future + decision-lag).
- Composite daily returns: `data/mn4_unified_0103/returns_IS.csv`,
  `returns_HOLDOUT.csv` (holdout last date 2026-06-30 — no Stage-3 leak).
- Quantstats tearsheets: `reports-portfolio-mn4/quantstats_UNIFIED-01-03_IS.html`,
  `quantstats_UNIFIED-01-03_HOLDOUT.html`.
- Full scorecard JSON: `data/mn4_unified_0103/scorecard.json`.

**MODEL NOTE (disclosed):** Engineered on Opus 4.8 (Claude Fable rate-limited;
user-directed). The composite construction + bit-by-bit proof were specified by
the orchestrator's brief; the implementation is byte-exact to the spec.

*— Engineer, MN4 UNIFIED-01-03, 2026-07-12. One signal, one book, one P&L,
bit-by-bit live parity proven. Forward paper-trade is the clean arbiter.*
