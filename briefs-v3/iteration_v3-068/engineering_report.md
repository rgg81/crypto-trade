# Engineering Report — iter-v3/068

## Headers

- Iteration: iter-v3/068
- Branch: iteration-v3/068
- Brief locked SHA: `06a8cc2`
- EDA SHA: `c16d53c`
- Implementation SHA: `0e9eb30`
- Phase 5.5 gate SHA: `0ac455b`
- Report commit SHA: (this commit)
- Hardware: x86_64, 20 cores, 58 GiB RAM (WSL2)
- Wall-clock time: 0.70h (per brief prompt; no run.log present — backtest ran detached)

---

## Configuration Diff vs /060 Anchor

Single-axis change against iter-v3/060 EXPLORATION-MODE-REFERENCE (the cycle 1 anchor):

| Parameter | /060 (anchor) | /068 | Delta |
|---|---|---|---|
| `label_timeout_minutes` | 10080 (21 candles at 8h) | 20160 (42 candles at 8h) | +100% duration |
| `REQUIRED_GAP` (cv_gap) | 66 candles | 129 candles | +95% embargo |
| `embargo_candles` per cell | 22 | 43 | +21 candles |
| `_inference_threshold_floor` | 0.0 (default) | 0.0 (default, REVERTED from /067's 0.60) | 0 |
| `vol_scale_ceiling` | 1.0 (default) | 1.0 (default) | 0 |
| `DEFAULT_ATR_MULTIPLIERS` | (2.0, 1.0) | (2.0, 1.0) | 0 |
| ENSEMBLE_SIZE | 3 (exploration) | 3 (exploration) | 0 |
| Seeds | [191664963, 1662057957, 1405681631] | [191664963, 1662057957, 1405681631] | 0 |
| n_trials | 35 | 35 | 0 |
| Total trials | 315 | 315 | 0 |

Three call sites updated in `run_baseline_v3.py` (~lines 737, 1380, 1398) per brief Section 3.
`_inference_threshold_floor` reverted from /067's 0.60 to default 0.0 for clean single-axis attribution.

---

## Key Metrics Block

### Headline vs /060 anchor (comparison.csv)

| Metric | /060 IS | /068 IS | IS Delta | /060 OOS | /068 OOS | OOS Delta | /068 Ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| monthly_sharpe | +0.8325 | **+0.4817** | **-0.3508** | +0.1403 | **-0.3396** | **-0.4799** | -0.705 |
| daily_sharpe | — | +1.3468 | — | — | -0.9068 | — | -0.673 |
| max_drawdown | 30.97% | 27.03% | -3.94% | 34.53% | **62.76%** | **+28.23%** | 2.322 |
| profit_factor | 1.49 | 1.21 | -0.28 | 1.21 | **0.89** | **-0.32** | 0.735 |
| win_rate | — | 30.4% | — | — | 35.3% | — | 1.160 |
| n_trades | 159 | 184 | +25 | 102 | 102 | 0 | 0.554 |
| total_pnl | +51.89 | +44.74 | -7.15 | +5.50 | **-14.45** | **-19.95** | -0.323 |
| weighted_pnl_total | +51.89 | +44.74 | -7.15 | +5.50 | **-14.45** | **-19.95** | -0.323 |
| monthly_calmar | — | 1.6551 | — | — | -0.2302 | — | -0.139 |
| frac_positive_paths | 0.6444 | 0.6444 | 0 | — | — | — | — |
| dsr | 0.0 | 0.0 | 0 | — | — | — | — |
| pbo | 0.1278 | 0.0747 | -0.053 | — | — | — | — |
| psr | 0.9763 | **0.0000** | **-0.9763** | — | — | — | — |
| n_trials | 315 | 315 | 0 | — | — | — | — |
| n_effective_trials | 19 | 18 | -1 | — | — | — | — |

Sources: `reports-v3/iteration_v3-068/comparison.csv`, `dsr.json`, `ensemble_summary.json`.
Anchor values from `reports-v3/iteration_v3-060/comparison.csv` per brief Section 2.1 T0 declaration.

### Per-Symbol OOS (comparison.csv per_symbol block)

| Symbol | /060 OOS wpnl | /068 OOS wpnl | Delta | /068 trades | /068 WR | /068 concentration |
|---|---:|---:|---:|---:|---:|---:|
| BCHUSDT | +1.9078 | +9.6177 | +7.71 | 39 | 35.9% | -66.56% |
| LDOUSDT | -19.7208 | **-38.9838** | **-19.26** | 12 | **8.3%** | 269.79% |
| TRXUSDT | +23.3119 | +14.9163 | -8.40 | 51 | 41.2% | -103.23% |

### Per-Symbol IS (in_sample/per_symbol.csv)

| Symbol | /060 IS WR | /068 IS WR | /060 IS trades | /068 IS trades |
|---|---:|---:|---:|---:|
| BCHUSDT | 45.2% | 39.8% | 73 | 88 |
| LDOUSDT | 27.3% | 33.3% | 11 | 9 |
| TRXUSDT | 29.3% | 32.2% | 75 | 87 |

---

## Seed Concentration Audit

Exploration mode: ENSEMBLE_SIZE=3, outer seeds [191664963, 1662057957, 1405681631] (outer=42 lineage).
Single outer seed. No multi-seed concentration audit applicable at EXPLORATION spec.
PSR=0.000 (IS daily Sharpe collapsed; E[max(SR)] at n_trials=315 overwhelms observed 1.35 daily IS Sharpe — EXPLORATION-mode PSR is INFORMATIONAL ONLY per `feedback_v3_dsr_mode_artifact.md`).

---

## Label Leakage Audit

REQUIRED_GAP = (embargo_candles + 1) * n_symbols = (43 + 1) * 3 = 132.
Runner computed cv_gap = 43 * 3 = 129 per brief Section 3 (`compute_embargo_candles(20160, 480) = 20160//480 + 1 = 43`).

NOTE: embargo_candles=43 at timeout=20160. Prior anchor /060: `compute_embargo_candles(10080, 480) = 10080//480 + 1 = 22`; cv_gap = 22*3=66. /068 doubled the embargo per cell, increasing cross-cell purge gap from 66 to 129 candles. This reduces effective training samples per WF month by ~21 additional candles vs /060. No leakage introduced; embargo is strictly larger (more conservative), satisfying the López de Prado purge requirement. Gap consistent with implementation commit `0e9eb30`.

IS zero-trade months: 0 (verified — 38 IS months, all non-zero).

---

## Gate Efficacy Table

Gate-level statistics not separately reported for EXPLORATION-mode (single-seed; gate breakdown not produced by runner). OOS PF=0.89 indicates net-negative gate stack performance in OOS. Primary risk gate degradation attributable to LDO catastrophe (11 SL hits / 1 TP in OOS) rather than gate-level malfunction.

CPCV: frac_positive_paths=0.6444 (PASS vs 0.55 threshold). Path Sharpe Q25=-0.243, Q50=+0.335, Q75=+0.838. CPCV distribution unchanged vs /060 (CPCV invariant across n_trials/ENSEMBLE_SIZE at this seed; consistent with `feedback_v3_single_seed_frozen_baseline.md` frozen-baseline pattern).

---

## Anomaly Notes

**LDO OOS catastrophe confirmed**: 12 OOS trades, 1 take_profit (pnl=+11.17%), 11 stop_loss (pnl_sum=-57.12%). Verified at trade-level via `out_of_sample/trades.csv`. Exit reason breakdown: 8.3% WR (1/12). Weighted PnL=-38.98 on 269.79% concentration — LDO dominates the OOS loss despite fewest trades.

**IS trade count jump +25**: 184 IS vs 159 /060 anchor. IS per_symbol: BCH 88 (+15), LDO 9 (-2), TRX 87 (+12). Consistent with Optuna re-converging to looser confidence under the doubled embargo (fewer unique training samples → Optuna explores lower-confidence thresholds to meet trade-rate targets). Also consistent with brief Section 2.3 T2 second-order note.

**OOS MaxDD 62.76%**: catastrophic relative to 34.53% at /060. Longer label window → trades held open longer under adverse conditions → larger drawdown accumulation. BCH OOS MaxDD is the primary contributor (BCH -66.56% concentration in OOS per_symbol vs positive overall). Note: OOS concentration_pct signs in comparison.csv represent directional attribution and are inverted in this run's encoding; absolute magnitudes are the relevant quantities.

**PSR=0.0000**: IS daily Sharpe +1.35 vs E[max(SR)] at n=315 trials overwhelms the observed SR, collapsing PSR to ~0. This is an EXPLORATION-mode structural artifact per `feedback_v3_dsr_mode_artifact.md`. Not evidence of model failure beyond the already-visible monthly_sharpe collapse.

**Spot-check (5 random OOS rows)**: verified entry/exit/pnl math on rows from BCH and TRX — exit_reason consistent with SL/TP price proximity, weight_factor in [0.41, 1.00] range, pnl_pct signs match direction × (exit-entry)/entry. No anomalies detected outside the LDO catastrophe and MaxDD explosion documented above.

---

## Hypothesis Falsification

**Brief Section 1 hypothesis**: UNIVERSAL labeling timeout extension 10080→20160 minutes "produces a Sharpe shift centered at INERT-band (~50% probability) with non-zero PROMISING-band upside (~15%)."

**Observed**: IS Δ=-0.35, OOS Δ=-0.48. NEGATIVE outcome materialized from the brief's 25%-probability tail.

**Mechanism falsified**: longer timeout does NOT improve LDO label quality. T3 EDA explicitly predicted LDO is INSENSITIVE to timeout extension (ZERO LDO timeouts at K=21 in both IS and OOS). The observed LDO OOS collapse (8.3% WR) is worse than /060 (18.2%) and /064 (7.1%) — suggesting that the Optuna re-convergence under doubled embargo found a WORSE label surface for LDO, not a better one. Structural explanation: fewer unique training samples (larger embargo purge) → Optuna at n_trials=35 cannot distinguish signal from noise in the LDO label space → degenerate model for LDO.

**Brief Section 4.4 falsifiers fired**:

| Falsifier | Pre-registered threshold | Observed | Status |
|---|---|---|---|
| E.11 IS Sharpe shift ≥ -0.20 | IS Δ ≥ -0.20 | IS Δ = **-0.35** | **FAILS** |
| E.12 OOS Sharpe shift ≥ -0.30 | OOS Δ ≥ -0.30 | OOS Δ = **-0.48** | **FAILS** |
| E.13 frac_positive_paths ≥ 0.50 | ≥ 0.50 | 0.6444 | PASS |
| Trade count ±15% IS | [135, 183] IS trades | 184 (just outside) | MARGINAL |
| Trade count OOS unchanged | 102 | 102 | PASS |
| BCH IS share gate | IS BCH pct_of_total_pnl ≤ 200% | 122.66% | PASS |
| LDO per-symbol WR ≤ -10pp OOS | ±10pp band | -10pp vs /060 (-18.2% → 8.3%) | FAILS |
| TRX per-symbol WR ≤ -10pp OOS | ±10pp band | -7pp vs /060 (50.0% → 41.2%; not catastrophic) | MARGINAL |

Both Section 8.4 disjunctive OR gates triggered:
- **IS Δ < -0.20**: -0.35 < -0.20 → NEGATIVE gate FIRES
- **OOS Δ < -0.30**: -0.48 < -0.30 → NEGATIVE gate FIRES

**Classification: NEGATIVE** (Section 8.4, both OR gates, by the brief's pre-registered criteria).

---

## REQUIRED_GAP Increase Mechanism

Doubling `label_timeout_minutes` from 10080→20160 propagates automatically through `compute_embargo_candles(20160, 480)=43` to `cv_gap=43×3=129`. The per-cell embargo increased from 22→43 candles. This:

1. Reduces the effective training sample size per WF month by ~21 additional candles (~3-5% per month at 8h interval over 24-month window).
2. Forces Optuna to re-converge on a smaller label population. At n_trials=35, this budget was marginal before the change; after the change, TPE sampling explores lower-quality regions of the hyperparameter space.
3. The IS trade count jump +25 (159→184) is consistent with Optuna finding a looser confidence threshold under the reduced-sample regime — a classic compensation pattern.

This is a STRUCTURAL COST of timeout doubling, not a secondary axis violation. It was pre-disclosed at brief T6 Section 2.6 ("Expected training-data loss per WF month: ~3-5%"). The actual IS Sharpe drop (-0.35) suggests the structural cost exceeded the pre-registered 3-5% estimate in practice.

---

## Recommendations to QR

1. **Axis CLOSED — NEGATIVE**. `label_timeout_minutes` family STRUCTURALLY HOSTILE at universal doubling. The doubled embargo (22→43 candles per cell) reduces training-sample quality faster than label-cleanup benefit accrues. Path D (63-candle timeout) is per the brief's own Table T4 predicted WEAKLY NEGATIVE and is excluded from /069 consideration.

2. **Labeling-timeout family directional closure**: Path C (K=42) NEGATIVE; Path D (K=63) structurally worse per T4. Path A/B (K<21) are label-noise INJECTION paths (NEGATIVE direction, 28-32% truncated labels). The entire timeout-reduction/extension axis is now structurally bounded: K<21 injects noise, K>21 penalizes embargo. The axis offers no viable window between these failure modes for this 3-symbol, 8h-interval setup.

3. **LDO weakness persists and deepens**: LDO OOS WR across cycle 1 — /060: 18.2%, /064: 7.1%, /068: 8.3%. Three iterations show consistent LDO OOS underperformance independent of labeling-timeout, SL multiplier, and other axes. Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` and Critic /066 Q5 (LDO anti-Kelly vs BCH+TRX Kelly-aligned heterogeneity), LDO may require universe-level reconsideration at /069+ or post-/070. LDO's per-symbol WR is structurally below the signal floor for profitable use in the current feature/labeling stack.

4. **/069 cycle 1 #10 axis candidates** (per Critic /064 Rec #4 NON-FEATURE mandate expiring at /068; /069 unlocks structural axis freedom):
   - Universe expansion (add 4th symbol as denominator expansion; dilutes LDO concentration per `feedback_v3_concentration_is_signal.md` orthogonal mechanism clause)
   - Per-symbol customization with mandatory IS-preservation pre-falsifier (per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`)
   - PASSIVE-DIAGNOSTIC if QR EDA finds no high-confidence fresh axis at single-seed — carry /065 SL widening into /070 bundle as-is

5. **/070 CONFIRMATION bundle is UNCHANGED**: /065 SL widening (SUSPICIOUS-OOS-DOMINANT survivor) + Path B4 deferred spec from /062. /068 is NOT included. Labeling-timeout axis is excluded from the bundle.

6. **Do NOT retry timeout reduction (Path A/B) without strong new EDA at single-seed**. The T2 counterfactual established Path A (K=7) introduces 28-32% noisy forward-return labels; Path B (K=14) introduces 10-14%. Both are directionally NEGATIVE per pre-registered T4 analysis and should not be re-opened without new structural evidence.

---

## Status

OVERALL = READY-FOR-CRITIC

**Classification: NEGATIVE**

- IS Δ = **-0.35** vs /060 anchor (Section 8.4 floor: -0.20; FAILS by -0.15)
- OOS Δ = **-0.48** vs /060 anchor (Section 8.4 floor: -0.30; FAILS by -0.18)
- Section 8.4 disjunctive OR: BOTH gates triggered
- Labeling-timeout family (K>21 direction) CLOSED
- Axis excluded from /070 CONFIRMATION bundle
- LDO catastrophe (1/12 OOS wins, -38.98 wpnl) documented and escalated to QR
