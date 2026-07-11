# MN4 IDEA-01 — Diary (TS-Momentum, blue-chip vol-scaled, β-hedged)

**Authored 2026-07-12.** QR+QE pair, Opus 4.8 model (Fable suspended — disclosed
per charter). IS-only; holdout never read; no Stage-3 data touched.

---

## 1. Decision: BANKS FOR PHASE-B REVEAL

5/6 IS gates pass; GATE-F (t_stat > 2.0) marginal at t=1.987 (actual two-tailed
p=0.047, below the 5% level). Per charter §"Process" all 10 ideas reveal
regardless of IS gate verdict; this construction banks for the Phase-B reveal
with disclosed limitations (CRASH structurally negative; DD brake fire-rate
65.7%; H1/H2 asymmetry). The orchestrator/Critic interprets the verdict.

---

## 2. Full IS scorecard

### 2.1 Headline (phase-agnostic mean stream, post-warmup, IS-only)

| metric | 1× cost | 2× GT | ratio |
|---|---|---|---|
| Sharpe | **+0.963** | +0.832 | 0.864 |
| t-stat | 1.987 | 1.721 | — |
| ann return | +23.46% | +19.30% | — |
| maxDD | **-34.42%** | -37.69% | — |
| win rate | 49.7% | 49.5% | — |
| final equity | 2.451 | 2.119 | — |
| n periods | 4658 | 4658 | — |

Cost-survival: Sharpe 2×/1× = 0.864 — the strategy retains 86% of its Sharpe at
2× cost. This is the cost-survival signature the charter emphasizes ("cost-
survival has been the binding constraint on this dataset").

### 2.2 Per-year Sharpe

| year | 1× | 2× GT |
|---|---|---|
| 2020 | +2.251 | +2.114 |
| 2021 | +2.290 | +2.162 |
| 2022 | -0.379 | -0.497 |
| 2023 | -0.187 | -0.323 |
| 2024 (H1 only) | **-1.041** | -1.183 |

2020-2021 are strong (the COVID-crash-recovery and the 2021 mania — TS-mom's
sweet spot). 2022 is mildly negative (the LUNA/FTX crash year — cross-sectional
momentum struggles when correlations spike). 2024 H1 is the worst (-1.04) — the
correlated mania resumption (BTC ETF approval, all majors ripping together).

### 2.3 Per-half Sharpe

| half | 1× | 2× GT |
|---|---|---|
| H1 (Jan-Jun) | -0.073 | -0.240 |
| H2 (Jul-Dec) | **+1.849** | +1.748 |

Strong H2 / weak H1. The strategy does well in Q3-Q4 (typically correction/chop
with wider cross-sectional dispersion) and poorly in Q1-Q2 (typically correlated
accumulation/mania with narrow dispersion). This is the classic cross-sectional-
momentum-in-crypto pattern.

### 2.4 Regime buckets (CRASH / MANIA / CHOP, market-only frozen rules)

| bucket | n | 1× Sharpe | 1× t | 1× cum | 2× Sharpe | 2× cum |
|---|---|---|---|---|---|---|
| CRASH | 570 | **-0.916** | -0.66 | **-8.09%** | -1.047 | -9.01% |
| MANIA | 890 | +0.896 | +0.81 | +19.68% | +0.740 | +15.12% |
| CHOP | 3198 | **+1.217** | +2.08 | +122.80% | +1.091 | +102.26% |

CHOP carries the book (+122.8% cum, Sharpe +1.22, t=2.08). MANIA is positive but
mild (+19.7% cum). CRASH is structurally negative (-8.09% cum); the Layer-2
throttle (gross=0.5 in CRASH) limits the loss but cannot flip it positive. This
is the canonical cross-sectional-momentum limitation in correlated crypto: when
the market falls uniformly, the rank partition longs the "least-down" names
(which still lose in absolute terms).

### 2.5 Neutrality (β_BTC / β_ETH, rolling + regime-bucket)

**Rolling book β (whole IS, 8h):**
- β_BTC mean = **-0.009**, median = -0.008, std = 0.025, [min=-0.071, max=+0.048]
- β_ETH mean = **-0.011**, median = -0.012, std = 0.026, [min=-0.100, max=+0.055]

**Regime-bucket β (direct OLS):**

| bucket | β_BTC | β_ETH |
|---|---|---|
| CRASH | +0.002 | -0.002 |
| MANIA | -0.010 | -0.017 |
| CHOP | -0.008 | -0.011 |

The cross-sectional β-null projection is essentially perfect: mean |β_BTC| ≈ 0.01
across all regimes, including CRASH (the hardest regime for neutrality). The
construction IS market-neutral by construction (beta_neutralize projects weights
onto {sum w = 0, sum w*β_BTC = 0} every rebal).

### 2.6 Turnover + cost coverage

| metric | 1× | 2× GT |
|---|---|---|
| turnover mean/candle | 0.0409 | 0.0406 |
| turnover ann (one-way) | **44.8×** | 44.4× |
| cost per candle (mean) | 3.07e-5 | 6.09e-5 |
| \|gross_ret\| per candle | 4.87e-3 | 4.83e-3 |
| coverage ratio (\|ret\|/cost) | **158.9×** | 79.4× |

Weekly rebal → 44.8× annualized one-way turnover (52 rebals/year × ~0.86 turnover
per rebal after the no-trade hysteresis from DD brake + vol-target). Coverage
ratio 159× means the gross edge covers cost 159 times over — cost is NOT a binding
constraint for this construction at 1×. At 2× GT, coverage is 79× — still huge.

### 2.7 Leak battery results (all PASS on actual IS panel + synthetic)

```
[leak] corrupt-future signal[:t0] bit-identical: True
[leak] corrupt-future scalar[:t0] bit-identical: True
[leak] PIT universe[:t0] bit-identical:         True
[leak] decision-lag equity[:t0+1] bit-identical: True
[leak] OVERALL: PASS
```

14/14 unit tests pass (`tests/test_mn4_idea01.py`); ruff clean. The decision-lag
test runs two full backtests with corrupted signal/scalar/beta at row ≥ t0 and
asserts the engine's realized equity through open[t0] is bit-identical — this is
the strongest possible lookahead check.

### 2.8 Risk-primitive behavior (Layer-2 + managed-variance + DD brake)

- **CRASH candles in IS:** 637 (12.9% of panel), spanning 2020-03-08 → 2024-05-01
- **crisis_scalar values:** 0.5 in CRASH (637 candles), 1.0 elsewhere (4292)
- **DD-brake fire-rate:** 3224 / 4908 rebals across 21 phases = **65.7%**
- **DD brake threshold / scale / recovery:** 0.15 / 0.50 / 0.075
- **vol-target:** ann=0.30, max_lev=1.5, lookback=63

**Dependency flag:** the DD brake fires 65.7% of the time, indicating the strategy
has chronic drawdown >7.5% for most of the IS. The brake is providing an effective
~50% gross haircut most of the time. Without the brake, maxDD balloons from -34.4%
to -47.7%. The brake IS doing critical work but its 65.7% fire-rate suggests the
underlying signal isn't strong enough to push equity to new highs consistently.

---

## 3. What worked

1. **Cross-sectional β-null projection (beta_neutralize) beats explicit hedge
   leg (HedgeOverlay).** Tested both: projection gives +1.12 phase-0 Sharpe /
   -44.5% maxDD vs explicit hedge +1.03 / -54.0%. The explicit hedge leg adds
   short-BTC churn that hurts in manias; the projection is cleaner. β_BTC mean
   is essentially zero (-0.009) across all regimes including CRASH.
2. **Wide universe (top-10) beats narrow (top-5).** Top-5 was too thin (max 6
   members) and gave unstable cross-sectional partitions. Top-10 was the smallest
   width that gave stable per-phase behavior.
3. **Multi-week lookback (84 = 4 weeks) is the sweet spot.** Tested 63/126/168/
   252; 84 dominates on Sharpe, maxDD, t-stat, 2022 crash performance, and 2×
   cost ratio. 84 is the conventional 1-month TS-mom window (Moskowitz/Pedersen).
4. **The 21-phase tranche averages out phase-lottery variance.** Per-phase
   Sharpes range -0.30 to +1.39; the phase-agnostic mean (+0.96) is the honest
   headline. The tranche design is doing exactly what feedback_rebal_phase
   mandates.
5. **Cost-survival is excellent** (2×/1× ratio 0.864, coverage 159×). The weekly
   cadence keeps turnover manageable (44.8× annualized one-way); cost is NOT a
   binding constraint for this construction.

## 4. What didn't work / structural limitations

1. **Canonical TS-mom is NOT expressible in the engine API.** The engine has
   rank-based weighting only; it cannot do per-name weights ∝ 1/σ_i. The
   construction is cross-sectional momentum with TS-mom signal, NOT canonical
   TS-mom. The per-name 1/σ_i tilt is preserved in the SELECTION (the signal IS
   trailing_return/realized_vol) but not in the per-name SIZE.
2. **CRASH regime is structurally negative (-0.916 Sharpe).** Cross-sectional
   momentum on correlated blue-chips cannot extract trend when the market falls
   uniformly. Pure TS-mom (sign-of-return weighted) would profit in CRASH, but
   the engine cannot express per-name sign-based weights. The Layer-2 throttle
   limits the loss to -8% cum but cannot flip it positive.
3. **2024-H1 mania is negative (-1.04 Sharpe).** Cross-sectional momentum loses
   in highly-correlated rising markets. Pure TS-mom would long everything; rank_neutral
   forces laggards short, which is a drag. This is the same architectural mismatch.
4. **t-stat 1.987 is marginal at the 2.0 threshold.** The IS signal is at the
   edge of conventional 5% significance. The actual two-tailed p-value (0.047)
   IS below 5%, but the round-number 2.0 threshold is marginally stricter. OOS
   regression-to-the-mean will likely pull t down to ~1.5.
5. **DD brake 65.7% fire-rate** = chronic-drawdown dependency. The brake is
   principle-anchored but the strategy leans on it heavily.

## 5. Lessons (generalizable)

1. **Engine API constraints are first-order.** The "canonical" construction in
   the literature often can't be expressed in the engine. Adapt early, document
   the deviation, and move on — don't fight the API.
2. **Cross-sectional momentum ≠ time-series momentum in correlated markets.**
   They diverge exactly when correlations spike (CRASH) or compress to ~1 (mania).
   Both are bad regimes for XS-mom; both are good regimes for TS-mom. The engine
   can only do XS-mom.
3. **The 21-phase tranche is HONEST but expensive.** The phase-agnostic mean
   (+0.96) is meaningfully lower than the best single phase (+1.39). A phase-0-
   only report would have overstated the strategy by ~50%. The tranche design
   prevents this overstatement.
4. **β-null projection > explicit hedge leg for market-neutrality.** Cleaner,
   lower turnover, better metrics. Hedge legs are a holdover from a long-only-
   plus-short-book mental model that doesn't fit the L/S cross-sectional case.
5. **Risk primitives compose non-linearly.** Crisis scalar + DD brake + vol-target
   together give Sharpe +0.96; any single primitive gives +0.67 to +0.82. The
   synergy is real but each primitive must be principle-anchored (round numbers)
   to avoid IS-overfit.

## 6. Next-iteration ideas (if this construction proceeds past Phase-B)

1. **Per-name sign-based weighting.** If the engine API can be extended (read-only
   reuse forbidden, but a NEW builder in our own namespace is allowed), a pure
   TS-mom construction with sign(trailing_ret) / σ_i per-name weights would
   address the CRASH regime (currently -0.92 Sharpe) directly. The infrastructure
   exists in the engine for `target_weights_*` builders — we just need our own.
2. **Regime-conditional universe contraction.** In CRASH, shrink the universe to
   {BTC, ETH, SOL} only (true blue-chip core) instead of the current uniform
   top-10. This implements the spec's "de-risk toward blue-chip core" more
   literally than the scalar-0.5 throttle.
3. **Add a short-term reversal overlay.** The H1 weakness (-0.07 Sharpe) suggests
   the strategy gives back gains in correlated accumulation phases. A 1-3 day
   reversal signal (fade extreme winners) layered on top of the TS-mom base
   might rescue H1.
4. **Try a different lookback per regime.** The 84-candle (4-week) lookback is
   IS-optimal. But CRASH might benefit from a SHORTER lookback (faster trend
   detection) while CHOP might benefit from a LONGER one (slower, more stable).
   A regime-conditional lookback is a structural change worth exploring.

## 7. Handoff to Phase-B reveal

The construction is byte-frozen in `analysis/portfolio/mn4_idea01_tsmom.py`. The
frozen constants are pinned by unit tests. The IS scorecard is honest (5/6 gates
pass + 1 marginal). The 2-year holdout (2024-07-01 → 2026-06-30) has not been
read. The single Phase-B reveal for IDEA-01 will run the frozen construction
through `blind_engine.run_backtest` on the holdout window and compare against
the IS gates. The orchestrator commits centrally; no git action by this pair.

**Files (all `mn4_idea01` namespaced):**
- `analysis/portfolio/mn4_idea01_tsmom.py` — frozen construction + driver
- `tests/test_mn4_idea01.py` — 14 leak-battery + engine-parity tests (all pass)
- `data/mn4_idea01/summary.json` — full IS scorecard (machine-readable)
- `data/mn4_idea01/{headline_rets_1x,headline_rets_2x,weights_avg_1x,
  per_phase_rets_1x,per_phase_rets_2x,signal,universe,gross_scalar,
  beta_btc_roll,beta_eth_roll,is_grid_ms}.npy` — saved arrays for reveal
- `briefs-portfolio-mn4/IDEA-01.md` — frozen spec + IS gates + decision principle
- `diary-portfolio-mn4/IDEA-01.md` — this document
