# iter-v1/010 — QR Phases 1-4 Summary

**Iteration**: iter-v1/010
**Track**: v1
**Date**: 2026-05-25
**Working directory**: `/home/roberto/crypto-trade/.worktrees/quant-research`
**Branch**: `iteration-v1/010`

## Axis (locked at /009 closeout)

**R5 vol-target ceiling per symbol** — `risk-primitive` family (UNUSED in v1 cycle-1 + cycle-2; first appearance).

Per /009 closeout 3-way convergence (LM Master + Critic + QR): R5 is preferred over R4 concentration cap per `feedback_v3_concentration_is_signal.md` v3/020 finding (concentration caps work as loss-stops, NOT proportional scaling; R5 is exposure ceiling — orthogonal mechanism).

## Phase 1 — EDA Headlines

### 1.1 Per-symbol IS NATR_14 distribution (`per_symbol_is_natr14_distribution.csv`)

Median NATR_14 across the v1 universe (5,012-5,714 IS candles per symbol):

| Symbol | mean | p10 | p25 | **p50** | p75 | p90 | p95 |
|---|---|---|---|---|---|---|---|
| BTCUSDT | 2.75 | 1.45 | 1.85 | **2.44** | 3.25 | 4.26 | 5.35 |
| ETHUSDT | 3.57 | 1.83 | 2.39 | **3.13** | 4.18 | 5.53 | 7.08 |
| LINKUSDT | 4.91 | 2.69 | 3.38 | **4.35** | 5.76 | 7.67 | 9.24 |
| LTCUSDT | 4.13 | 2.12 | 2.73 | **3.65** | 4.94 | 6.65 | 7.91 |
| DOTUSDT | 4.60 | 2.24 | 2.93 | **4.12** | 5.49 | 7.44 | 9.09 |

The original /009 brief's "recommend 2.5% (mid of crypto realized NATR range)" framing was based on an estimate. The actual per-symbol p50 ranges from 2.4% (BTC) to 4.4% (LINK). The universe-weighted average p50 is **~3.5%**, and the universe p75 is **~4.7%**.

### 1.2 Candle-level fire rate at candidate vol_target_pct values (`candle_level_fire_rate_by_target.csv`)

R5 fire rate (cap < 1.0) per (symbol, vol_target_pct):

| vol_target | BTC | ETH | LINK | LTC | DOT |
|---|---|---|---|---|---|
| 2.0% | 69.3% | 86.2% | 98.3% | 92.7% | 93.8% |
| 2.5% | 47.8% | 70.6% | 93.5% | 80.6% | 85.1% |
| 3.0% | 31.1% | 54.1% | 82.9% | 67.6% | 73.5% |
| 3.5% | 19.4% | 39.0% | 72.4% | 54.1% | 62.1% |

**At 2.5%, fire rate is 48-93%; the cap fires constantly on LINK and DOT and ETH/LTC, hitting F2 mis-calibration ceiling of 80%.**

### 1.3 Trade-level fire rate on baseline trade roster (`trade_level_fire_rate_simulated.csv`)

Portfolio-aggregated R5 fire rate (cap < 1.0) on the v0.v1-baseline trade roster (IS=620 trades / OOS=189 trades — one IS trade dropped due to NATR-NaN window-start):

| vol_target | IS fire | OOS fire | mean cap (IS) | mean cap (OOS) |
|---|---|---|---|---|
| 2.0% | 85.2% | 82.0% | 0.686 | 0.715 |
| 2.5% | 66.6% | 64.6% | 0.798 | 0.829 |
| 3.0% | 48.4% | 45.0% | 0.874 | 0.907 |
| 3.5% | 35.0% | 27.5% | 0.923 | 0.954 |
| **4.0%** | **22.6%** | **15.3%** | **0.954** | **0.977** |
| 4.25% | 18.4% | 11.6% | 0.964 | 0.983 |

**Trade-level fire-rate ∈ [10%, 60%] (the F2 reasonable-activation band) is achieved ONLY at vol_target ∈ [3.5%, 4.5%].** The brief's initial 2.5% target is OUTSIDE the activation band on both halves.

### 1.4 Oracle Sharpe-delta simulation (`simulated_sharpe_delta_oracle.csv`)

Per /054 ORACLE EDA mandate: R5 is STATELESS (cap depends only on NATR_14 at open_time, NOT on persistent state). Oracle EDA on prior trade roster is VALID for stateless gates.

Monthly Sharpe deltas vs baseline (IS=0.091, OOS=0.171):

| vol_target | IS Δ oracle | OOS Δ oracle | IS fire rate | OOS fire rate |
|---|---|---|---|---|
| 2.0% | -0.100 | -0.051 | 85.2% | 82.0% |
| 2.5% | -0.086 | -0.050 | 66.6% | 64.6% |
| 3.0% | -0.082 | -0.042 | 48.4% | 45.0% |
| 3.5% | -0.071 | -0.027 | 35.0% | 27.5% |
| **4.0%** | **-0.056** | **-0.020** | **22.6%** | **15.3%** |
| 4.25% | -0.048 | -0.015 | 18.4% | 11.6% |
| 4.5% | -0.042 | -0.012 | 14.7% | 7.9% |

**All candidates show NEGATIVE oracle Sharpe delta.** This is the well-known signature of a variance-reducing risk primitive applied on a baseline-with-edge: R5 caps disproportionately on the highest-vol moments, which is where LINK (the top OOS contributor) takes its largest trades. Reducing LINK's average position size mechanically reduces total return faster than it reduces variance — see `feedback_v3_concentration_is_signal.md` (proportional scaling is wrong primitive for concentration handling at 3-symbol universe; v1's 5-symbol case is structurally analogous but less severe).

**Counter-evidence per Section 7 mandate:** the oracle EDA assumes Optuna's hyperparameter selection is FROZEN. Inside /010's actual backtest, Optuna re-optimizes against R5-scaled rewards. If the model learns to favor lower-vol entries when caps fire less, the OOS delta could close to neutral or marginally positive (Pareto improvement possible IFF the model can substitute high-vol high-confidence entries with lower-vol high-confidence entries — open empirical question).

## Phase 2 — Labeling

UNCHANGED — `atr_tp_multiplier=3.5`, `atr_sl_multiplier=1.75`, `label_timeout_minutes=10080` (7 days), `vol_natr_21` ATR column for label sizing.

## Phase 3 — Symbol Selection

UNCHANGED — `V1_BASELINE_UNIVERSE = (BTCUSDT, ETHUSDT, LINKUSDT, LTCUSDT, DOTUSDT)`. 5-symbol pooled-A.

## Phase 4 — Risk Wiring Design

### 4.1 R5 mathematics

```
R5_cap_ratio = min(1.0, vol_target_pct / max(NATR_14, 0.01))
```

where `NATR_14` is `vol_natr_14` (already in V1_FEATURE_COLUMNS_PRUNED; 14-period NATR in percent at 8h cadence ≈ 4.67-day volatility).

The cap is **multiplicative** on the pre-existing weight_factor pipeline:

```
weight_factor = vt_scale × R2_cap_ratio × R5_cap_ratio × (signal.weight / 100)  # VT off case
weight_factor = vt_scale × R2_cap_ratio × R5_cap_ratio                          # VT on case (v1 baseline path)
```

### 4.2 Calibrated vol_target_pct: **4.0%**

**Revised from brief Section design recommendation of 2.5% based on Phase 1 EDA.** Rationale:

1. **Trade-level fire rate at 4.0%**: IS 22.6%, OOS 15.3% — both within F2 reasonable-activation band [10%, 60%].
2. **Best-of-grid oracle Sharpe deltas**: IS Δ -0.056 (within F3 catastrophic -0.10), OOS Δ -0.020 (within F1 -0.05).
3. **Mean cap intensity at 4.0%**: 0.954 IS / 0.977 OOS — modest scaling consistent with "ceiling" semantics, NOT "constant brake" semantics.
4. **Anchored on universe-mean p75 (≈ 4.7%)**: capping at p75 leaves the top 25% of high-vol periods subject to R5 — textbook crypto risk-management calibration.

The 2.5% recommendation in the design intent was reasonable for "mid of crypto realized NATR range" assumption, but the EDA reveals NATR_14 distributions skew higher than that estimate (universe p50 ≈ 3.5%, p75 ≈ 4.7%). The EDA designed a sharper experiment than the original spec.

### 4.3 Where R5 fires (sequencing)

R5 fires AFTER R2 inside `backtest.py:378-388`:

```python
vt_scale = 1.0
if config.vol_targeting:
    vt_scale = compute_vt_scale(...)
# R2 — drawdown-triggered position scaling (only Model E active)
if config.risk_drawdown_scale_enabled:
    dd_pct = max(0.0, peak_weighted_pnl - cum_weighted_pnl)
    if dd_pct > trigger and anchor > trigger:
        r2_scale = 1.0 - span * (1.0 - floor)
        vt_scale = vt_scale * r2_scale
# R5 — vol-target ceiling (NEW; ALL MODELS)
if config.risk_r5_vol_target_enabled:
    natr = r5_natr_lookup.get((sym, ot), float("nan"))
    if not np.isnan(natr):
        r5_scale = min(1.0, config.risk_r5_vol_target_pct / max(natr, 0.01))
        vt_scale = vt_scale * r5_scale
order = create_order(sym, signal, ..., vt_scale=vt_scale)
```

**Double-attenuation guard (Model E)**: at Model E, R2 fires 71% IS / 63% OOS at mean ~0.33 (BASELINE_V1.md "Risk Gate Fire Rates"). R5 at 4.0% fires ~15-22% on DOT (Model E's symbol). The joint product can compound: when both fire simultaneously on DOT, weight_factor floor ≈ 0.33 × ~0.6 = 0.20. Section 7 Failure Mode 3 covers this.

### 4.4 Implementation path — cleanest design (3 file edits)

The /010 src/ diff is mechanically minimal:

1. **`src/crypto_trade/backtest_models.py` (+5 lines)**: add `BacktestConfig` fields:
   ```python
   risk_r5_vol_target_enabled: bool = False
   risk_r5_vol_target_pct: float = 4.0
   ```

2. **`src/crypto_trade/backtest.py` (+12 lines)**: at backtest start, build `r5_natr_lookup: dict[(str, int), float]` from feature parquets (mirrors lgbm.py's `_month_natr` loading pattern at lgbm.py:634, but indexed per (symbol, open_time) candle); insert R5 block after R2 at the existing `vt_scale = vt_scale * r2_scale` line.

3. **`run_baseline_v1.py` (+2 lines)**: set `risk_r5_vol_target_enabled=True, risk_r5_vol_target_pct=4.0` in the BacktestConfig in `run_model`.

This is opt-in via the config field defaults — restoring `risk_r5_vol_target_enabled=False` (the default) preserves byte-identical baseline behavior on all prior iterations. **Same opt-in discipline as /003's Component 2/3 trunk merge.**

**NO live-engine sync required for EXPLORATION.** Live wiring (engine.py R5 mirror) is a CONFIRMATION-spec deliverable IF /010 reaches CONFIRMATION (which requires PROMISING gate).

### 4.5 Determinism

R5 is purely deterministic given the NATR_14 feature parquet:
- NATR_14 is computed past-only (14-period rolling on past closes; pandas-ta default — already audited in v1 baseline)
- Lookup is keyed by `(symbol, open_time)` — bit-identical for same data extent
- No new random state introduced (no seed, no Optuna call, no RNG)
- F1 trade roster determinism: with R5 OFF, the /010 backtest must reproduce baseline trade roster bit-exactly (sanity check for QE Phase 6)

## Phase 5 — Brief Output

See `briefs-v1/iteration_v1-010/research_brief.md`.

## Concerns Carried to Phase 5.5 + 6.0

1. **Oracle Sharpe Δ is negative across ALL candidates.** F1 expects OOS Δ < -0.05 for NEGATIVE. The EDA's best candidate (4.0%) shows oracle OOS Δ = -0.020 — well within tolerance — but real Optuna re-optimization may produce divergence in either direction. The brief Section 8 PROMISING gate has been left at the original +0.05 floor (intentionally conservative) but the EXPECTED OOS Δ given oracle EDA is closer to -0.020 to +0.05, NOT to a strong positive number. **PROMISING is unlikely; PROMISING-INERT or marginal NEGATIVE is plausible.** This is honestly reported up-front.

2. **Brief original spec said "recommend 2.5%". I revised to 4.0% per EDA.** This is the "EDA designs the sharpest experiment" mandate. If LM Master + Critic reviewing the brief disagree with 4.0%, the brief explicitly leaves an alternative path at 3.5% (next-best calibrated value; trade-level OOS fire rate 27.5%, within band; OOS oracle Δ -0.027). Section 11 lists 4.0% as PRIMARY and 3.5% as alternate.

3. **F2 redefinition vs /005 closeout's "F2 demoted to STRUCTURAL-only".** /010's F2 is fire-rate-band-check, NOT feature-importance-Spearman. This is the v1 catalog's first F2 in the new sense (post-/005 demotion). Critic Check 4 may want explicit framing.

4. **Capacity-fit-noise hazard at single-seed=42**: per /005 lesson 6, wider-bounds-and-features add variance at single-seed. R5 is FEWER-trades semantics, not wider-bounds — but it changes Optuna's reward distribution. Brief Section 7 includes "Optuna re-optimization with scaled rewards may discover new IS-overfit basins" as Failure Mode 4.

5. **HIGH-RISK declaration**: R5 changes Optuna's training-objective domain through weight_factor scaling — qualifies as HIGH-RISK per axis taxonomy. Brief Section 2.5 declares HIGH-RISK with mitigation = pre-commit to /011 multi-seed CONFIRMATION IF /010 PROMISING. 6th-consecutive HIGH-RISK iteration without auto-mandate-multi-seed trigger (rule fires at 3+ HIGH-RISK with >1σ negative deltas in a row; /005-/009 had 5 HIGH-RISK NEGATIVES — closer to threshold than ever, but mechanism for /010 is structurally different so single-seed is justified per LM Master /009 confidence-MEDIUM).

6. **Methodology debt — N_eff PCA refactor was CLOSED at /008.** No new methodology debt accrues at /010.

7. **DEGENERATE_PREDICTOR detector** (added at /008): MUST run on /010 reports. R5 does not introduce new sources of degenerate prediction but the detector is now standard per /008.

8. **Phase 6.0 pre-flight scan list**: src/ diff is 3 files (~19 lines net new) — well within minimum-footprint discipline. No race conditions (R5 is in the same thread as R2 inside `run_backtest`). No new look-ahead surface (NATR_14 is past-only). No methodology ordering issue.

## Deliverables (Phases 1-5)

1. `analysis/iteration_v1-010/r5_vol_target_calibration.py` — committed analysis script
2. `analysis/iteration_v1-010/per_symbol_is_natr14_distribution.csv` — Phase 1.1 evidence
3. `analysis/iteration_v1-010/candle_level_fire_rate_by_target.csv` — Phase 1.2 evidence
4. `analysis/iteration_v1-010/trade_level_fire_rate_simulated.csv` — Phase 1.3 evidence
5. `analysis/iteration_v1-010/simulated_sharpe_delta_oracle.csv` — Phase 1.4 evidence
6. `analysis/iteration_v1-010/simulated_sharpe_delta_finer_grid.csv` — finer-grid supplement
7. `analysis/iteration_v1-010/trade_level_finer_grid.csv` — finer-grid trade-level
8. `analysis/iteration_v1-010/run.log` — script stdout (tee'd)
9. `briefs-v1/iteration_v1-010/qr_phases_1_4_summary.md` — this file
10. `briefs-v1/iteration_v1-010/research_brief.md` — Phase 5 brief (next)
