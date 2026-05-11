# Engineering Report — iter-v3/051

## Status: READY-FOR-CRITIC

EXPLORATION-NEGATIVE-BORDERLINE — IS Sharpe +0.4506 falls below the PATH A threshold
(IS Δ = -0.0595 vs /028 +0.5101; PATH A requires Δ ≥ +0.05) and is also above the
PATH C-clean hard floor (Δ < -0.10 not triggered). OOS Sharpe +0.5891 is within the
PATH A band (OOS Δ = +0.0838 vs /028 +0.5053; PATH A requires Δ ≥ -0.20). IS-OOS daily
Sharpe ratio = 1.1478, inside the [0.5, 2.0] band (no suspicious-OOS pattern). fracdiff
importance ranks: BCH 12/15, LDO 11/15, TRX 11/15 — PATH B (INERT) threshold of >13/15
in ALL symbols is NOT fired; fracdiff was learned. None of the pre-registered four path
triggers map cleanly to the observed result: PATH A fails (IS Δ = -0.06; threshold +0.05),
PATH B fails (ranks well above 13), PATH C-clean fails (IS not < -0.10, OOS not < -0.30),
PATH C-suspicious fails (ratio within band). This is a genuine BORDERLINE: fracdiff
provides signal but the REVERT-induced IS compression (-0.06 vs baseline) pulls the IS
below the PATH A lift requirement.

The CRITICAL finding — independent of fracdiff — is LDO structural confirmation: LDO OOS
weighted_pnl = -17.44 (13 trades, 23.1% WR) after FULL REVERT of per-symbol ATR, primitive
10, and ALGO. This is NOT the iter-v3/047-level customization artifact; it is the 3-symbol
/028-architecture result. LDO's OOS signal generator is persistently negative independent
of any per-symbol customization layer.

---

## Headers

- Iteration: iter-v3/051
- Branch: iteration-v3/051
- Setup commit SHA: c0ebe21
- Brief SHA: 6697f95
- Hardware: x86_64, 60 GB RAM, WSL2
- Wall-clock time: 1.28h (well within 2h EXPLORATION cap)

---

## Configuration Diff vs BASELINE_V3.md

```
BASELINE_V3.md anchor (iter-v3/028): IS +0.5101 / OOS +0.5053 (multi-seed mean)

REVERT (system-level mandate from feedback_v3_per_symbol_lifts_oos_breaks_is.md):
  V3_MODELS: BCH + LDO + TRX (3 symbols; ALGO DROPPED — was 4-sym at iter-v3/033-050)
  V3_ATR_MULTIPLIERS_PER_SYMBOL: {} EMPTY (cleared ALGO 2.0/1.5 + LDO 2.0/1.5)
  block_long_for: () EMPTY (cleared BCH LONG block from iter-v3/047 primitive 10)
  REQUIRED_GAP: 66 = (21+1)*3 (recomputed from 88 = (21+1)*4 for 3-sym universe)

SINGLE NEW AXIS (iter-v3/051 axis under test):
  V3_FEATURE_COLUMNS_TOP_N: 15 features (ADD fracdiff_d05_close as 15th)

UNCHANGED from BASELINE_V3.md:
  regime_momentum_signed_5d PRESENT (iter-v3/028 edge ingredient preserved)
  V3_FEATURES_PER_SYMBOL: {} empty
  DEFAULT_ATR_MULTIPLIERS: (2.0, 1.0)
  adx_threshold: 20.0 (global)
  adx_threshold_per_symbol: {} empty
  zscore_threshold: 2.0
  OOS_CUTOFF_DATE: 2025-03-24  — IMMUTABLE
  training_months: 24           — IMMUTABLE

EXPLORATION spec:
  ENSEMBLE_SIZE: 5 (inner seeds [42, 123, 456, 789, 1001])
  outer_seeds: 1 (EXPLORATION-spec)
  n_trials: 35 per cell (default per feedback_v3_exploration_n_trials_35.md)
  Total Optuna trials: 525 = 3 symbols × 5 inner seeds × 35 trials
  Run command: uv run python run_baseline_v3.py --seeds 1 --n-trials 35 --clean-oof
```

---

## Key Metrics Block

### Single-Seed Results (seed 42; EXPLORATION-spec)

| metric | in_sample | out_of_sample | ratio |
|---|---:|---:|---:|
| monthly_sharpe | +0.4506 | +0.5891 | 1.307 |
| daily_sharpe | +0.9685 | +1.1116 | 1.148 |
| max_drawdown | 37.37% | 32.75% | 0.876 |
| profit_factor | 1.1552 | 1.1485 | 0.994 |
| win_rate | 32.02% | 39.58% | 1.236 |
| n_trades | 178 | 96 | 0.539 |
| total_pnl | 30.33 | 17.43 | 0.575 |
| monthly_calmar | 0.8114 | 0.5321 | 0.656 |
| dsr | 0.0000 | — | — |
| pbo | 0.1168 | — | — |
| psr | 1.0000 | — | — |
| n_trials | 525 | — | — |
| n_effective_trials | 19 | — | — |

### Delta vs BASELINE_V3.md (iter-v3/028 multi-seed mean reference)

| Metric | iter-v3/051 (1-seed) | iter-v3/028 baseline | Delta | PATH Gate |
|---|---:|---:|---:|---|
| IS monthly_sharpe | +0.4506 | +0.5101 | **-0.0595** | PATH A requires Δ ≥ +0.05 — MISS by 0.11 |
| OOS monthly_sharpe | +0.5891 | +0.5053 | **+0.0838** | PATH A requires Δ ≥ -0.20 — PASS |
| IS-OOS daily Sharpe ratio | — | — | **1.1478** | [0.5, 2.0] band — PASS |

### Delta vs iter-v3/045 Cycle 3 Anchor (single-seed comparator for context)

| Metric | iter-v3/045 (1-seed) | iter-v3/051 (1-seed) | Delta |
|---|---:|---:|---:|
| IS monthly_sharpe | +0.7459 | +0.4506 | -0.2953 |
| OOS monthly_sharpe | +3.5259 | +0.5891 | -2.9368 |

The cycle 3 anchor's single-seed lottery characteristics (IS +0.75 / OOS +3.53) do not
survive the full REVERT to /028 architecture. This is expected; iter-v3/050 multi-seed
CONFIRMATION already confirmed those numbers are seed-42-specific artifacts.

---

## fracdiff_d05_close Feature Investigation

### Importance Rank Per Symbol

| Symbol | fracdiff rank | fracdiff importance | Rank 1 feature | Rank 1 importance | PATH B threshold (>13) |
|---|---:|---:|---|---:|---|
| BCH | **12 / 15** | 54.0 | max_dd_window_50 | 138.8 | NOT fired |
| LDO | **11 / 15** | 109.4 | ret_skew_200 | 186.0 | NOT fired |
| TRX | **11 / 15** | 91.0 | range_realized_vol_50 | 202.4 | NOT fired |
| Portfolio | **13 / 15** | 254.4 | max_dd_window_50 | 489.6 | NOT fired |

**fracdiff_d05_close was learned by all 3 per-symbol models.** Mid-table placement
(ranks 11-12 across symbols) is consistent with the "moderate signal strength, not
dominant" prediction from the brief. PATH B (PROMISING-INERT, requiring rank >13 in
ALL 3 symbols) is conclusively not triggered.

Comparison to brief prediction:
- BCH: predicted "top-10 in 15" → observed 12/15. Miss by 2 ranks; directionally correct
  (within top half), not top-10.
- LDO: predicted "top-12" → observed 11/15. PASS; strongest univariate ρ (-0.051)
  matched with highest importance score (109.4) among the 3 symbols.
- TRX: predicted "top-12" → observed 11/15. PASS; flat importance distribution meant
  the new feature slotted mid-table as predicted.

### IC Carve-Out Verification

ic_matrix.csv (pooled IS across 3 symbols) confirms:
- fracdiff_d05_close vs vwap_dev_20: 0.1178 — well below 0.70 strict gate.
- fracdiff_d05_close vs regime_momentum_signed_5d: 0.1478 — below 0.70 strict gate.
- Max pairwise |IC| with existing 14 features: 0.1803 (with range_realized_vol_50).

**All post-carve-out IC values clear the strict 0.70 gate.** The EDA-level per-symbol
IC concerns (LDO 0.7381 with vwap_dev_20 in IS subset) did not manifest in the pooled
IS runtime matrix; the pooled correlation is 0.1178, confirming the EDA estimated a
symbol-specific extreme that averages out across the broader IS sample. Carve-out was
conservative (correct to apply it given EDA evidence; runtime confirms it was not needed
at the pooled level).

### Signal vs No-Signal Comparison

fracdiff was learned (ranks 11-12) but produced no IS lift. The IS Δ = -0.06 vs
/028 baseline is the signal that Optuna chose hyperparameter configurations at the
15-feature matrix that are slightly worse on IS than the baseline 14-feature matrix.
This could reflect: (a) competition for split budget between fracdiff and similar features
(vwap_dev_20, regime_momentum_signed_5d — both price-path derived), or (b) statistical
noise at n_trials=35 single-seed (the [+0.05, +0.30] IS lift prediction was uncertain
at single-seed EXPLORATION spec).

The OOS positive result (+0.0838 Δ vs /028) is within the predicted band [-0.20, +0.30]
and directionally encouraging, but single-seed OOS results have the frozen-baseline
lottery caveat (established in feedback_v3_single_seed_frozen_baseline.md).

---

## LDO Structural Concern — Critical Finding

### OOS Performance History at Seed 42

| Iteration | LDO config | LDO OOS wpnl | LDO OOS trades | LDO OOS WR | Notes |
|---|---|---:|---:|---:|---|
| iter-v3/047 | ATR (2.0, 1.5) + primitive 10 | -17.44 | — | — | Frozen-baseline |
| iter-v3/049 | ATR (2.0, 1.5) + primitive 10 | -17.44 | — | — | Bit-identical to /047 |
| iter-v3/050 | ATR (2.0, 1.5) + primitive 10 (seed 42) | -19.13 | 12 | 33.3% | Per /050 report |
| **iter-v3/051** | **DEFAULT ATR (2.0, 1.0) + NO primitive 10** | **-17.44** | **13** | **23.1%** | **REVERT** |

The iter-v3/051 result is decisive: LDO OOS weighted_pnl = -17.44 after FULL REVERT to
iter-v3/028 architecture. All per-symbol customizations (LDO ATR widening 2.0/1.5 from
iter-v3/045, BCH LONG block from iter-v3/047, ALGO from iter-v3/033) have been removed.
The default 3-sym /028 configuration still produces persistently negative LDO OOS results.

**LDO OOS net_pnl_pct = -22.57%, avg_pnl_pct = -1.74% per trade, WR = 23.1% (3/13).** A
23.1% win rate from 13 OOS trades over ~14 months is not within normal variance of the
signal; it reflects a signal generator that is producing directionally wrong predictions
for LDO in the OOS period.

**IS comparison**: LDO IS = 11 trades, 27.3% WR, net_pnl_pct = -5.99%, avg_pnl_pct =
-0.55%. LDO is IS-marginally-negative too (IS contribution = -14.96% of total IS PnL).
The "IS-positive ATR customization" claimed at iter-v3/045 appears to have been single-seed
specific: at iter-v3/051 (default ATR, different Optuna draw) LDO IS is also negative.

**Implication for iter-v3/052**: LDO removal from V3_MODELS is now the highest-priority
investigation for cycle 4 #2. The EDA at iter-v3/051 analysis scripts (SHA `290f37b`)
rejected LDO removal on the axis of IS-Δ for the full /050 config (the axis_a_ldo_attribution.csv
showed IS Δ -0.015 from removing LDO at /050). But the /051 result changes the calculus:
in the /028-reverted 3-symbol universe, LDO IS is -14.96% of total PnL (a drag, not a
contribution). A fresh EDA on the /051 trade roster (LDO IS -5.99% PnL / IS 27.3% WR)
provides new quantitative basis for LDO removal that was not available at the /050 EDA stage.

---

## System-Level REVERT Verification

The REVERT successfully restored iter-v3/028 architecture. Verification table:

| Dimension | Expected (iter-v3/028 reference) | Observed iter-v3/051 | Status |
|---|---|---|---|
| V3_MODELS | 3 symbols (BCH, LDO, TRX) | 3 symbols — confirmed | PASS |
| V3_ATR_MULTIPLIERS_PER_SYMBOL | {} empty | {} empty — confirmed | PASS |
| block_long_for | () empty | () empty — confirmed | PASS |
| REQUIRED_GAP | 66 = (21+1)*3 | 66 — confirmed | PASS |
| n_trials | 35 (EXPLORATION default) | 525 total = 3×5×35 | PASS |
| IS monthly_sharpe (single-seed reference) | ≈ [+0.40, +0.65] (estimated /028 1-seed range) | +0.4506 | WITHIN range |
| OOS monthly_sharpe (single-seed reference) | ≈ [+0.30, +0.80] | +0.5891 | WITHIN range |
| IS trades (reference /028 = 156 multi-seed mean) | 130-200 predicted | 178 (+14.1% vs ref) | PASS |
| OOS trades (reference /028 = 95 multi-seed mean) | 70-110 predicted | 96 | PASS |
| OOS max_dd | — | 32.75% (vs /028 23.53% multi-seed mean) | Slight elevation; single-seed lottery |

The IS Sharpe of +0.4506 sits at the lower portion of the estimated 1-seed range
[+0.40, +0.65], consistent with the REVERT restoring a /028-like starting point. The
additive effect of fracdiff_d05_close did not produce the predicted +0.05 to +0.30 IS
lift; the net IS result landed -0.06 below the /028 multi-seed mean (which itself
represents an averaged-up version of single-seed draws). The REVERT mechanism worked
as designed; the fracdiff axis alone was insufficient to push IS above the /028
multi-seed mean at single-seed n_trials=35.

---

## Falsifier Check (per brief Section 4 / Section 8 pre-registered criteria)

| Falsifier | Threshold | Observed | Fired? |
|---|---|---|---|
| IS Δ < -0.10 (PATH C-clean — IS regression) | Δ < -0.10 | Δ = -0.0595 | NOT FIRED |
| OOS Δ < -0.30 (PATH C-clean — OOS regression) | Δ < -0.30 | Δ = +0.0838 | NOT FIRED |
| fracdiff rank > 13/15 in ALL 3 symbols (PATH B — INERT) | all > 13 | BCH=12, LDO=11, TRX=11 | NOT FIRED |
| IS-OOS daily Sharpe ratio outside [0.5, 2.0] (PATH C-suspicious) | outside [0.5, 2.0] | 1.148 | NOT FIRED |
| IS trade count change > 30% vs /028 ref (cascade) | > 30% | +14.1% | NOT FIRED |
| IS Δ ≥ +0.05 AND OOS Δ ≥ -0.20 (PATH A — PROMISING) | both must hold | IS: -0.0595 FAIL | NOT TRIGGERED |

**No pre-registered path fires.** The result is a BORDERLINE state between PATH C-clean
and PATH A:
- IS Δ = -0.0595: inside the no-man's-land between PATH C-clean floor (-0.10) and PATH A
  ceiling (+0.05). Neither path is triggered by pre-registration.
- OOS Δ = +0.0838: satisfies PATH A (≥ -0.20) and satisfies PATH C (not < -0.30).
- IS-OOS ratio = 1.148: clean (within band).
- fracdiff importance: clearly learned (11-12/15); PATH B not applicable.

The pre-registered Section 8 did not include an explicit BORDERLINE path. The closest
applicable classification is NEGATIVE-clean by the IS-axis criterion alone, but the IS
Δ = -0.0595 is ABOVE the PATH C-clean threshold of -0.10. The QR must classify in
Phase 7; the Engineer's assessment is BORDERLINE (single-seed IS noise vs genuine
axis inadequacy — not distinguishable at n_trials=35, 1 seed).

**Saturation rule implication (pre-registered)**: The saturation rule in brief Section 8
states "if iter-v3/051 produces PATH C-clean OR PATH C-suspicious, fracdiff_d05_close
UNIVERSAL axis is CLOSED for cycle 4." PATH C-clean is NOT triggered (IS Δ = -0.0595
does not cross the -0.10 floor). PATH C-suspicious is NOT triggered. The fracdiff axis
is therefore NOT closed by pre-registered saturation rule; the BORDERLINE result leaves
the QR with discretion in Phase 7.

---

## Pathway Classification Hypothesis

Based on the falsifier check and pre-registered paths:

**Engineer assessment: BORDERLINE — between NEGATIVE-borderline and PROMISING-marginal.**

The evidence for each interpretation:

**NEGATIVE-borderline reading (stronger weight)**:
- IS Δ = -0.06 below the /028 multi-seed mean. At CONFIRMATION (multi-seed), this -0.06
  single-seed result would need to survive seed dispersion. Given the pattern from cycles
  2 and 3 (single-seed IS lifts that collapse at multi-seed), a single-seed IS regression
  of -0.06 likely maps to a multi-seed IS regression of similar or larger magnitude.
- fracdiff importance at rank 12-11 is mid-table — the feature competes with and partially
  displaces regime_momentum_signed_5d (which falls to rank 14/15 BCH, 15/15 LDO, 12/15
  TRX, 15/15 portfolio). Adding fracdiff may be cannibalizing regime_momentum signal
  rather than adding independent IS lift.
- LDO IS is negative even in the 28-reverted configuration (IS WR 27.3%, -14.96% PnL
  share), meaning the 3-symbol universe IS Sharpe depends heavily on BCH (104.05% IS
  PnL share) with TRX barely positive (+10.91%).

**PROMISING-marginal reading**:
- OOS Δ = +0.08 is positive and directionally clean (IS-OOS ratio 1.15).
- fracdiff was learned at ranks 11-12 across 3 symbols; the feature is not INERT.
- The IS -0.06 miss vs PATH A is only 0.11 Sharpe points above PATH C-clean, suggesting
  a small upward IS noise draw at multi-seed could push into PROMISING territory.
- fracdiff ADF stationarity and univariate signal (|ρ| = 0.038-0.051 all significant)
  are valid IS evidence — the feature's absence of IS lift at n_trials=35 single-seed
  may be Optuna search noise rather than a genuine signal absence.

The QR's Phase 7 decision will determine whether cycle 4 continues with fracdiff as a
candidate (PROMISING-marginal → test at multi-seed CONFIRMATION as a bundle ingredient)
or reverts to the pre-registered PATH C-clean action (pivot to regime_momentum_signed_3d
UNIVERSAL at iter-v3/052). The pre-registered saturation rule provides the QR with the
decision framework.

---

## Per-Symbol Decomposition

### IS Per-Symbol

| Symbol | trades | win_rate | net_pnl_pct | avg_pnl_pct | pct_of_total_IS_pnl |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 90 | 43.3% | +41.70% | +0.463% | **+104.05%** |
| TRXUSDT | 77 | 35.1% | +4.37% | +0.057% | +10.91% |
| LDOUSDT | 11 | 27.3% | -5.99% | -0.545% | -14.96% |

BCH carries 104% of IS PnL; TRX marginally positive; LDO IS-negative (-14.96%).
The 3-symbol IS Sharpe of +0.4506 is almost entirely BCH-driven.

### OOS Per-Symbol

| Symbol | trades | win_rate | net_pnl_pct | avg_pnl_pct | pct_of_total_OOS_pnl | concentration_pct |
|---|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 37 | 43.2% | +31.14% | +0.842% | **+160.32%** | **+135.36%** |
| TRXUSDT | 46 | 41.3% | +10.85% | +0.236% | +55.85% | +64.71% |
| LDOUSDT | 13 | 23.1% | -22.57% | -1.736% | -116.17% | **-100.07%** |

BCH drives 160% of OOS PnL. LDO cancels -116% of OOS PnL. BCH and TRX positive
contributions are net-diminished by LDO to produce the +17.43 total OOS weighted_pnl.
The OOS Sharpe of +0.5891 is the residual after LDO's drag on BCH+TRX combined
performance.

---

## regime_momentum_signed_5d Importance Analysis

| Symbol | regime_momentum rank | regime_momentum importance | fracdiff rank (for comparison) |
|---|---:|---:|---:|
| BCH | 14 / 15 | 47.6 | 12 / 15 (54.0) |
| LDO | 15 / 15 | 101.0 | 11 / 15 (109.4) |
| TRX | 12 / 15 | 89.0 | 11 / 15 (91.0) |
| Portfolio | 15 / 15 | 237.6 | 13 / 15 (254.4) |

regime_momentum_signed_5d is dead last (15/15) at LDO and portfolio levels; second-to-last
at BCH. fracdiff_d05_close marginally outranks regime_momentum at ALL 3 symbols and portfolio
(254.4 vs 237.6 portfolio; 109.4 vs 101.0 LDO; 91.0 vs 89.0 TRX; 54.0 vs 47.6 BCH). The
two features appear to occupy a similar bottom tier in the importance distribution, with
fracdiff consistently (though narrowly) higher. This suggests partial collinearity with the
existing 14-feature stack rather than an independent signal dimension.

The iter-v3/028 edge ingredient (regime_momentum) reaching rank 15/15 at portfolio in the
REVERTED 3-symbol universe is a new diagnostic: at iter-v3/050 the feature ranked 14/14
(last) in the 4-symbol universe. The REVERT did not recover regime_momentum signal strength;
it remains at the bottom of the importance distribution across all per-symbol models.

---

## OOS Monthly Profile

| Month | trades | pnl_pct | Status |
|---|---:|---:|---|
| 2025-04 | 6 | +4.91% | Positive |
| 2025-05 | 8 | +11.51% | Positive |
| 2025-06 | 10 | +14.36% | Positive |
| 2025-07 | 9 | +0.40% | Positive |
| 2025-08 | 15 | **-10.73%** | Negative (worst month) |
| 2025-09 | 6 | +5.03% | Positive |
| 2025-10 | 12 | **-9.83%** | Negative |
| 2025-11 | 6 | **-7.63%** | Negative |
| 2025-12 | 3 | +4.11% | Positive |
| 2026-01 | 5 | -1.09% | Negative |
| 2026-02 | 5 | -2.30% | Negative |
| 2026-03 | 4 | +5.34% | Positive |
| 2026-04 | 5 | +0.62% | Positive |
| 2026-05 | 2 | +2.73% | Positive |

Positive months: 9 of 14 (64.3%). Negative months: 5 of 14. No zero-trade OOS months.
Worst month: 2025-08 (-10.73%, 15 trades). Three consecutive negative months Aug-Oct
2025 (-10.73%, -9.83%, -7.63%) representing the primary OOS drawdown cluster.

---

## CPCV Analysis

45 paths generated (REQUIRED_GAP = 66, n_paths=45, 3-symbol universe).

| Statistic | Value |
|---|---:|
| Paths positive | 29 of 45 (64.4%) |
| Median path Sharpe | +0.335 |
| PBO (per-cell mean) | 0.1168 |
| frac_positive_paths | 0.644 |
| Q25 path Sharpe | -0.243 |
| Q75 path Sharpe | +0.884 |

PBO = 0.1168 is well below the 0.40 threshold (PASS). frac_positive_paths = 64.4% is
a mild improvement vs iter-v3/050 (53.3%), reflecting that the REVERT to the
3-symbol universe (BCH+LDO+TRX) produces more consistent path-level generalization
than the 4-symbol universe from cycle 3 (where ALGO + LDO negative drags were more
dispersed). The 3-symbol CPCV at 64.4% is roughly comparable to iter-v3/028 baseline
level (which was the first successful CONFIRMATION). The CPCV signal is mildly
constructive despite the IS Sharpe shortfall.

---

## Label Leakage Audit

REQUIRED_GAP = 66 = (21 + 1) × 3 symbols (REVERT from 88 = (21+1)×4 for 4-symbol universe).
timeout_candles = 21 (7 days × 3 × 8h candles/day). n_symbols = 3.
Gap formula: (timeout_candles + 1) × n_symbols = 22 × 3 = 66. Applied in CPCV. PASS.

Sacred constants verified:
- OOS_CUTOFF_DATE = 2025-03-24: UNCHANGED
- training_months = 24: UNCHANGED
- ensemble_seeds = [42, 123, 456, 789, 1001]: UNCHANGED

---

## Gate Efficacy Table

| Gate | Parameter | IS fire-rate (est) | OOS fire-rate | Notes |
|---|---|---|---|---|
| BTC trend filter | lookback=42, threshold=15% | post-hoc | 32 trades killed (seed 42) | 32 BTC-killed OOS trades of ~128 candidates ≈ 25% |
| OOD z-score gate | zscore_threshold=2.0, **15-D space** | embedded | embedded | UP from 14-D (fracdiff_d05_close added) |
| ADX gate | threshold=20.0 global; per-symbol={} | embedded | embedded | No per-symbol override at /051 |
| Primitive 10 — BCH direction block | block_long_for=() | 0% | 0% | REVERTED; gate in code but not firing |
| Per-symbol ATR | DEFAULT (2.0, 1.0) all syms | embedded | embedded | All syms at default per REVERT |
| Per-symbol cap | enable_per_symbol_cap=False | DISABLED | DISABLED | Closed per iter-v3/020 |
| Regime gate | enable_regime_gate=False | DISABLED | DISABLED | Closed per iter-v3/022 |

BTC trend killed 32 OOS trades (from seed_summary.json). This is ~25% of OOS candidates
(assuming ~128 candidates before BTC filter for 3-symbol universe), consistent with prior
v3 iterations. The gate is active and material.

---

## Seed Concentration Audit

Single-seed EXPLORATION (1 outer seed, seed=42).

| Metric | Value |
|---|---:|
| OOS monthly Sharpe | +0.5891 |
| OOS max_dd | 32.75% |
| OOS calmar | 0.5321 |
| OOS trades | 96 |
| max_concentration_pct (OOS) | 67.65% |
| BTC killed OOS | 32 |

Max concentration 67.65% = BCH (135.36% weighted_pnl share; the 67.65% is the max
concentration on a percentage-of-OOS-total basis). BCH concentration remains high in
the 3-symbol universe — consistent with iter-v3/028 baseline (76.47% TRX dominant at
multi-seed). The 3-symbol universe concentrates risk by design; this is expected.

---

## Anomaly Notes

1. **fracdiff OOS IC discrepancy vs EDA**: The per-symbol EDA computed IC(fracdiff,
   vwap_dev_20) = 0.7381 for LDOUSDT. The runtime ic_matrix.csv (pooled IS) shows
   IC = 0.1178 for the same pair. The discrepancy arises because the EDA computed
   per-symbol IS-subset IC on the full LDO parquet slice (5+ years), while the runtime
   computes pooled cross-symbol IC on the rolling IS window used for the last training
   month. Both are valid; the runtime pooled IC is the operationally relevant number.
   The carve-out was correctly applied at EDA stage; the runtime confirms it was
   conservative (the pool IC is well below 0.70).

2. **regime_momentum_signed_5d displacement by fracdiff**: fracdiff outranks
   regime_momentum at all 3 symbols and portfolio (BCH: 54.0 vs 47.6; LDO: 109.4 vs
   101.0; TRX: 91.0 vs 89.0; portfolio: 254.4 vs 237.6). Both features rank in the
   bottom tier. This suggests partial collinearity: fracdiff may be capturing a similar
   "price-path memory" signal to regime_momentum, and the two features are competing
   for split budget rather than contributing orthogonal information.

3. **LDO IS negative at default ATR**: LDO IS WR = 27.3%, avg_pnl = -0.545% per trade
   at DEFAULT ATR (2.0, 1.0). At iter-v3/045, the per-symbol ATR customization (2.0,
   1.5) produced IS Sharpe lift for LDO (per that iteration's report). At iter-v3/051
   with DEFAULT ATR and 35 trials, LDO IS is also negative. Two interpretations: (a)
   the iter-v3/045 IS lift was seed-42-specific Optuna draw with the ATR customization
   enlarging the IS Sharpe via favorable hyperparameter lottery, or (b) LDO IS with
   default ATR and n_trials=35 is genuinely negative, and the /045 improvement was
   partially real (ATR customization legitimately improving LDO IS signal capture). The
   iter-v3/052 LDO removal EDA should compare LDO IS at the full /051 backtest output
   vs a /051-without-LDO counterfactual.

4. **OOS daily Sharpe (1.1116) exceeds IS daily Sharpe (0.9685)**: ratio = 1.148.
   Not suspicious (within [0.5, 2.0] band); however OOS > IS at the daily level is
   unusual for most trading systems. At v3 it reflects the OOS window containing a
   favorable BCH period (Q2 2025 large positive months: Apr +4.91%, May +11.51%, Jun
   +14.36%) that inflates OOS daily Sharpe. The monthly Sharpe (OOS +0.5891 > IS
   +0.4506) shows the same pattern.

5. **n_effective_trials = 19**: consistent with prior v3 EXPLORATION results (iter-v3/049:
   19; iter-v3/050: 18). Low n_eff relative to n_trials=525 indicates that most trial
   paths are highly correlated — the true independent trial count is ~19, not 525. DSR
   structural artifact: at n_trials=525, E[max_SR] >> observed SR → DSR = 0.0.

---

## Recommendations to QR for Phase 7 / iter-v3/052

1. **BORDERLINE classification is the QR's decision (Phase 7)**: The pre-registered paths
   do not cleanly resolve the result. PATH C-clean requires IS Δ < -0.10; observed IS
   Δ = -0.0595. PATH A requires IS Δ ≥ +0.05; observed IS Δ = -0.0595. The QR must
   classify using discretion anchored in the pre-registered brief Section 8 framework:
   (a) apply the spirit of PATH C-clean ("IS regression at single-seed = no lift") →
   pivot to regime_momentum_signed_3d at /052; or (b) note that fracdiff was learned
   (ranks 11-12) and the IS shortfall is within single-seed n_trials=35 noise → defer
   fracdiff to CONFIRMATION bundle evaluation.

2. **LDO removal is now the highest-priority cycle 4 axis**: LDO OOS weighted_pnl =
   -17.44 after FULL REVERT to /028 architecture. The prior EDA rejection at iter-v3/051
   (axis_a_ldo_attribution.csv: IS Δ -0.015 from removing LDO at the /050 config) is
   now superseded by /051 evidence: LDO IS is also negative at /028-reverted config
   (-14.96% IS PnL share). A fresh EDA on /051 trade roster should compute the
   3-vs-2-symbol comparison: (BCH+TRX only) vs (BCH+LDO+TRX). If the BCH+TRX IS
   Sharpe > +0.5101 (baseline), LDO removal at cycle 4 #2 is justified.

3. **regime_momentum_signed_5d signal review**: The iter-v3/028 edge ingredient now ranks
   15/15 (dead last) at portfolio and LDO levels, and 14/15 at BCH. If the 3-symbol
   REVERT does not recover regime_momentum signal (as this iteration shows), the QR
   should evaluate whether the feature is still contributing edge in the /028 baseline
   or whether it was a cycle-1 iteration effect that has since decayed.

4. **fracdiff carryforward option (if QR classifies PROMISING-marginal)**: If the QR
   decides fracdiff is a cycle 4 bundle candidate (marginal PROMISING reading), it should
   be combined with the LDO removal investigation at /052 rather than carried forward
   solo. The IS Δ from fracdiff alone (-0.06) is not sufficient; a possible LDO removal
   (+IS Sharpe uplift from removing a drag) may compound positively with fracdiff.

5. **Cycle 4 cadence**: iter-v3/051 is cycle 4 #1 of 10 EXPLORATIONs. iter-v3/061 is
   the cycle 4 CONFIRMATION (per feedback_v3_strict_10_to_1_cadence.md). The cadence
   requires 9 more EXPLORATIONs before CONFIRMATION regardless of how iter-v3/051 is
   classified.

---

## Status

OVERALL=READY-FOR-CRITIC
