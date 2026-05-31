# iter-v1/041 — EDA Findings

**Date**: 2026-05-31
**QR**: claude-opus-4-7 (Project Mode v1)
**Mode**: EXPLORATION cycle-5 #8/10
**Axis family**: `labeling` — TIGHTEN-WITHIN-TRIPLE-BARRIER (first attempt in v1 cycles 1-5; sister to /014 σ_t source change and /035/036 trend-scanning)
**Direction**: SHRINK absolute barrier bandwidth 50% while preserving TP/SL ratio = 2.0
**EDA script**: `analysis/iteration_v1-041/eda.py` (commit-pending)

---

## Section 1 — Anchor & Axis Specification

Baseline (`v0.v1-baseline-corrected`, `BASELINE_V1.md` commit `f8bc12c`):
- Per-model ATR-multiplier triple-barrier (NATR_21 × close × multiplier)
  - Model A (BTC + ETH pool): `atr_tp=2.9 / atr_sl=1.45` (ratio 2.0)
  - Models C (LINK), D (LTC), E (DOT): `atr_tp=3.5 / atr_sl=1.75` (ratio 2.0)
- Timeout: 21 × 8h candles = 7 days
- 621 IS trades / 189 OOS trades.

Proposed (`iter-v1/041`): uniform tighten across all models to `atr_tp=1.5 / atr_sl=0.75` (ratio 2.0 preserved). Optional pair: `min_data_in_leaf` floor bump 20 → 50 per /038 LM Master Phase 7.4 Rec 2 (defends against over-fit on noisier shorter-horizon labels).

> **Honest deviation note**: the task brief framed this as "baseline TP=2.0 / SL=1.0 → 1.5 / 0.75". The v1 ATR-multiplier baseline is `2.9/1.45` (Pool A) and `3.5/1.75` (C/D/E) — not `2.0/1.0`. The proposed `1.5/0.75` is therefore a deeper compression than the task header implied. The downstream projection bands in this EDA are anchored on the **actual baseline multipliers**, so they overshoot the task brief's pre-stated band.

---

## Section 2 — Baseline Exit-Reason and Duration Distribution (IS)

Per-symbol exit-reason shares (IS, 621 trades; from `analysis/iteration_v1-041/baseline_distribution.csv`):

| Symbol | Trades | TP share | SL share | Timeout share | dur_p50 (candles) | dur_p90 |
|---|---|---|---|---|---|---|
| BTCUSDT | 113 | 23.9% | 62.8% | 13.3% | 8.0 | 21.0 |
| ETHUSDT | 145 | 25.5% | 54.5% | 20.0% | 9.0 | 21.0 |
| LINKUSDT | 146 | 17.8% | 50.7% | 31.5% | 11.5 | 21.0 |
| LTCUSDT | 124 | 20.2% | 50.8% | 29.0% | 11.0 | 21.0 |
| DOTUSDT | 93 | 21.5% | 50.5% | 28.0% | 13.0 | 21.0 |
| **Portfolio** | **621** | **21.7%** | **53.8%** | **24.5%** | — | — |

**Reading**: 24.5% IS timeouts — substantial fraction of labels resolve weakly. Tightening barriers should bite into this share AND accelerate per-candle barrier resolution for the 75% of trades that already hit TP/SL within 11 median candles. BTC has lowest timeout share (13.3%) so will see smallest absolute lift from this axis.

---

## Section 3 — Per-Symbol Trade-Count Projection at TP=1.5 / SL=0.75

Mechanism — under GBM/Brownian assumption, expected forward-bars-to-barrier-resolution scales as `(barrier_distance)²`. Density ratio (labels-per-cell) therefore scales as `(cur_tp / proposed_tp)²`:

| Symbol | Cur atr_tp | Cur atr_sl | Raw density ratio | Count mult LOW (cap×0.85) | Count mult HIGH (cap×1.10) | Projected IS LOW | Projected IS HIGH |
|---|---|---|---|---|---|---|---|
| BTCUSDT | 2.9 | 1.45 | 3.74× | 2.55× | 3.00× | 288 | 339 |
| ETHUSDT | 2.9 | 1.45 | 3.74× | 2.55× | 3.00× | 369 | 435 |
| LINKUSDT | 3.5 | 1.75 | 5.44× | 2.55× | 3.00× | 372 | 438 |
| LTCUSDT | 3.5 | 1.75 | 5.44× | 2.55× | 3.00× | 316 | 372 |
| DOTUSDT | 3.5 | 1.75 | 5.44× | 2.55× | 3.00× | 237 | 279 |

The capped band reflects a soft ceiling of `3.0×` baseline trades (the R3 OOD gate is unchanged and prunes ~30% of candidates in either regime, so density growth saturates). Per-symbol cap also reflects: every label resolved earlier frees the next candidate sooner but does NOT create candidates that R3 would otherwise reject.

**Portfolio bands (EDA-anchored, IS-only)**:
- **IS**: baseline 621 → projected **[1582, 1863]** trades (≈ 2.55× – 3.00× lift)
- **OOS**: baseline 189 → projected **[480, 567]** trades (same multiplier applied as upper bound check)

**Reconciliation with task header band [800, 1050] IS / [240, 320] OOS**: the task header anchored on `atr_tp=2.0 → 1.5` (1.78× density ratio). My anchor on `2.9 → 1.5` (3.74×) and `3.5 → 1.5` (5.44×) is the actual baseline. The honest EDA projection is therefore **higher** than the task brief band. If the next QR/Critic Phase 6.0 decides to anchor the proposal to a smaller tighten step (e.g. `atr_tp 2.9 → 2.2 / 1.45 → 1.10` for Pool A and `3.5 → 2.625 / 1.75 → 1.3125` for C/D/E — a uniform 25% shrink), the trade-count projection contracts back into the task's stated band [800, 1050] IS / [240, 320] OOS. I leave this calibration question for the Phase 5 brief.

---

## Section 4 — Exit-Reason Reroute Projection

Conservative (exit-time only, doesn't see intra-trade extrema):

| Symbol | tight TP earlier | tight SL earlier | timeout→TP | timeout→SL | still timeout |
|---|---|---|---|---|---|
| BTCUSDT | 23.9% | 62.8% | 0.9% | 1.8% | 10.6% |
| ETHUSDT | 25.5% | 54.5% | 1.4% | 0.7% | 17.9% |
| LINKUSDT | 17.8% | 50.7% | 8.9% | 0.7% | 21.9% |
| LTCUSDT | 20.2% | 50.8% | 8.9% | 4.8% | 15.3% |
| DOTUSDT | 21.5% | 50.5% | 4.3% | 1.1% | 22.6% |

**Reading**: at tight barriers, 80-90% of trades resolve as TP/SL EARLIER (in the same polarity). 1-9% of baseline timeouts flip to TP (rewarded migration), 0.7-4.8% flip to SL (additional loss). The "still timeout" share is conservative because it excludes trades whose intra-trade extrema would have hit the tighter band — actual flips will be higher than the table shows. **The dominant effect is acceleration of resolution, not exit-reason reassignment.** This is the load-bearing claim under the tighten axis.

---

## Section 5 — PnL Magnitude Projection

Mean absolute net PnL per trade (IS):
- Baseline: **5.70%** per trade
- Tight: **3.03%** per trade
- Ratio: **0.53×** (50% smaller per-trade swings, as expected from halving the barrier magnitude)

Mechanism: smaller barriers reduce per-trade PnL roughly proportionally. The portfolio-level Sharpe ratio depends on whether (a) win-rate holds up under shorter-horizon noise, (b) trade-count rises enough to net positive. The Sharpe-side arithmetic:

Approximate Sharpe scaling under tighten:
- Per-trade Sharpe ∝ E[r] / σ[r]
- E[r] scales ~0.5× (half the bandwidth)
- σ[r] scales ~0.5× (same bandwidth)
- Single-trade Sharpe ≈ unchanged in expectation IF win-rate holds
- Portfolio Sharpe ∝ √(N) × per-trade Sharpe (independence approx; not strictly true with overlap)
- N scales 2.55-3.00×, so √N scales 1.60-1.73×
- **Portfolio Sharpe upper-bound multiplier ≈ 1.6× IF the edge survives noise**

But: win-rate under shorter forward windows is the killer risk. Crypto 8h candles have material chop; reducing the TP barrier by 50% means random-walk noise can hit it without the structural signal driving it. Empirically v3 trend-scanning at horizons {5, 8, 13, 21} candles showed signal degradation below 5 candles. At median dur 8-13 candles baseline, tightening to TP=1.5×NATR may compress median forward-window into the 4-6 candle range — into noise territory.

---

## Section 6 — F1 Modal Prediction Band

Given:
- Trade-count lift +2.55× – 3.00× (well above ≥130 OOS / ≥10/month floor; saturates R3 OOD ceiling)
- PnL magnitude shrink 0.5×
- Median-forward-window compression risk (5-10 → 3-6 candles approx) entering chop noise

Verdict-distribution priors (LM Master /037+/038 calibrated cycle-5 priors; FLAT-on-axis-novelty):

| Verdict | Prior | Rationale |
|---|---|---|
| **PROMISING-CLEAN** (F1 OOS Δ ≥ +0.10) | **18%** | If shorter-horizon TP/SL edge survives noise AND √N scaling materialises, OOS Sharpe lifts toward +0.85-1.0 |
| PROMISING-INERT-FAV (F1 OOS Δ ∈ [+0.05, +0.10)) | 16% | Density lift compensates for win-rate softening; near-flat |
| **INERT-NO-EFFECT** (F1 OOS Δ ∈ (-0.05, +0.05)) | **22%** | Chop noise cancels √N count gain; portfolio Sharpe unchanged |
| NEG-OVER-FILTER (F1 OOS Δ ∈ [-0.30, -0.05]) | 14% | min_data_in_leaf=50 mitigation under-shoots; over-fit on noisy labels mildly degrades |
| **NEG-CATASTROPHIC** (F1 OOS Δ < -0.30) | **30% MODAL** | Win-rate collapses below 35% on short labels; basin migration produces IS-over-fit; OOS noisy losses dominate |

Combined PROMISING: **34%**. Combined NEG: **44%**. **NEG-CATASTROPHIC is modal at 30%.**

**Rationale for NEG-MODAL prior**:
- /035 trend-scan (shorter-horizon labels) was bimodal NEG-CAT-bundle — cycle-5 has precedent for shorter-horizon labeling collapses.
- BASELINE_V1.md exit-reason distribution shows IS SL share 53.8% — already a tough chop environment for the model. Tightening reduces the buffer.
- 50% PnL magnitude cut without proportional Sharpe-per-trade preservation = pure noise amplification.
- Cycle-5 LM Master directional accuracy 1/4 = 25% so flat-tier discipline applies (no prior tilts above 35% absent strong empirical anchor).

---

## Section 7 — Pre-Registered Falsifiers (load-bearing for Phase 7.5)

F-AXIS #1 (wiring): IS trade count ≥ 1500 — proves tighter labels generated and dispatched. **<1300 → BLOCK-PENDING-FIX silent fallback to baseline.**

F-AXIS #2 (cell-rate): per-(cohort, training-window) label count median ≥ 1000 (vs baseline ~360) — proves the density lift mechanism fired. **Median <800 → mechanism didn't bite as predicted; downgrade to NEG-MECHANICAL.**

F-AXIS #3 (PRIMARY F1 outcome): OOS monthly Sharpe Δ vs baseline +0.6637 — bands per Section 6.

F-AXIS #4 (PnL magnitude): mean |net_pnl_pct| ∈ [2.5%, 3.5%] OOS. **Outside band → PnL scaling assumption violated; revisit before any interpretation of F-AXIS #3.**

F-AXIS #5 (win-rate floor): OOS WR ≥ 35% portfolio. **<35% → chop-noise dominance confirmed empirically; axis CLOSED for v1.**

---

## Section 8 — Key Risk and Caveats

1. **Noise vs signal at shorter horizons (THE central risk)**. The proposed `1.5 × NATR_21` TP is ~3% of close for BTC (NATR_21 p50 = 2.46% × 1.5 = 3.69%) — well within single-candle BTC range at 8h. The TP becomes a near-immediate hit for any candle with even moderate intra-candle volatility, decoupling TP from directional signal. **This is the strongest reason NEG-CAT is modal.**

2. **R3 OOD gate ceiling**. Density growth saturates near 3× because R3 prunes the same proportion. The trade-count band assumes R3 is unchanged — TRUE per axis spec.

3. **min_data_in_leaf=50 mitigation is double-edged**. Higher leaf floor → less over-fit on noisy labels (good) but also less granularity → may collapse important feature-tier signal at the noise-dense barrier scale (bad). Net effect at v1 EXPLORATION budget (single seed, n_trials=18) is ambiguous.

4. **Per-trade fee fraction balloons**. Baseline mean |PnL| 5.70% with 0.1% fee = 1.8% fee drag per trade. Tight mean |PnL| 3.03% with 0.1% fee = 3.3% fee drag — **nearly DOUBLE the fee-to-edge ratio**. If the per-trade edge collapses by 50% but the fee stays absolute, the Sharpe-after-fees is more sensitive than before.

5. **No deterministic-equivalence guarantee**. /014 σ_t labeling did NOT match baseline at any window. /041's ATR-multiplier-shrink axis is closer in family to baseline than /014's mode swap, but the labels are still different per (cohort, candle). Baseline-determinism check vs `iteration_v1-baseline` will NOT match by design.

---

## Section 9 — Recommendation to Phase 5 Brief Author

The bold central question: **does v1 LightGBM extract more edge from denser short-horizon labels, or does the loss surface become too noisy?**

Three viable Phase 5 axis variants (ordered by EDA support):

1. **A. Original task spec — uniform tighten to atr_tp=1.5 / atr_sl=0.75 + min_data_in_leaf=50.** Strong novelty (first TIGHTEN axis in v1). Highest probability of catastrophe (30% modal NEG-CAT). Strong falsifier structure available.

2. **B. Half-tighten — atr_tp=2.2 / atr_sl=1.10 Pool A; atr_tp=2.6 / atr_sl=1.3 C/D/E (25% shrink uniform).** Lower R3-saturation pressure (density ratio 1.74×, projected IS ~1080 — INSIDE task header band [800, 1050]). Lower per-trade fee-drag risk. Likely less informative on the bold central question.

3. **C. Asymmetric — keep atr_tp at baseline; tighten atr_sl only to 50% (atr_sl=0.725 Pool A; 0.875 C/D/E).** Increases SL hit rate while preserving TP polarity — favors win-rate stability if model edge is in direction-call not magnitude. Most novel within axis family; orthogonal to all prior /014/035/036 axes.

**EDA-anchored recommendation: variant A (original task spec) for boldness and falsifier strength** — the experiment is precisely the one the v1 catalog has never run, and the falsifier structure resolves the bold central question with the same wall-clock budget. Phase 5 brief should explicitly cite the NEG-MODAL prior and pre-commit Phase 7.5 Critic to evaluate F-AXIS #4 (PnL magnitude) BEFORE F-AXIS #3 (Sharpe) to disambiguate chop-noise dominance from genuine edge.

---

## Section 10 — Numerical Output Artifacts

- `analysis/iteration_v1-041/baseline_distribution.csv` — per-symbol per-sample IS+OOS exit-reason / duration / PnL stats
- `analysis/iteration_v1-041/projection_is.csv` — per-symbol IS projection at tight barriers
- `analysis/iteration_v1-041/projection_oos.csv` — per-symbol OOS projection (informational; not used in EDA decision)
- `analysis/iteration_v1-041/summary.csv` — portfolio bands

EDA script `analysis/iteration_v1-041/eda.py` is committed before this brief.
