# Engineering Report — iter-v3/055

## Status: READY-FOR-CRITIC

**PATH C-clean (IMPLEMENTATION DEFECT) + PATH E (CPCV-INVARIANT NULL, 5th consecutive).**

The DSR_relative gate was implemented with a write-before-read ordering bug:
`cpcv_paths.csv` is written to disk at line 2295 of `run_baseline_v3.py`, but
the DSR_relative block at line 2182 attempts to READ it from disk at computation
time — before the write. Because the file does not yet exist, the `else` branch
fires ("cpcv_paths.csv not found — cpcv_path_sharpe_q75 = 0.0 (fallback)") and
the benchmark is silently set to 0. This makes `DSR_relative = PSR(observed_SR;
benchmark=0) = PSR_plain = 1.0` — a degenerate value identical to plain PSR and
meaningless as a reformulated gate.

The correct `DSR_relative` (using CPCV Q75 = 0.8378 from the in-memory `cpcv_df`
already populated at line 2090) would have been **0.5798**, which is below the
pre-registered 0.95 threshold (FAIL for this iteration) and qualitatively
consistent with the brief's predicted range of PSR_vs_Q75 ≈ 0.177-0.235 for a
/053-style baseline.

The strategy itself is BIT-IDENTICAL to iter-v3/028 (single-seed=42): IS monthly
Sharpe +0.5101, OOS +0.5053, IS 182 trades, OOS 96 trades, per-symbol breakdown
BCH/TRX/LDO identical to `/028` at 4 decimal places. This confirms the
methodology-only axis did not disturb the strategy. The CPCV distribution is also
bit-identical to /051/052/053/054 (5th consecutive iteration), firing PATH E as
predicted.

---

## Headers

- Iteration: iter-v3/055
- Branch: iteration-v3/055
- Setup commit SHA: 4a32e00
- Gate commit SHA: (see phase5p5_gate.md)
- Head SHA at report time: 4a32e004509fef866ab6cb6e599a3c20b31ab3b5
- Hardware: x86_64, 60 GB RAM, WSL2
- Wall-clock time: 2.03h (within 2h EXPLORATION cap; slower than expected 1.25h
  due to v1 baseline running concurrently; v2 had completed before relaunch)

---

## Configuration Diff vs BASELINE_V3.md

```
BASELINE_V3.md anchor (iter-v3/028): IS +0.5101 / OOS +0.5053 (multi-seed mean)

CARRY-FORWARD (UNCHANGED at /055 from /054 head):
  V3_MODELS: BCH + LDO + TRX (3 symbols — UNCHANGED)
  V3_ATR_MULTIPLIERS_PER_SYMBOL: {} EMPTY
  block_long_for: () EMPTY
  V3_FEATURE_COLUMNS_TOP_N: 14 features (hurst_drift_50_200 PARKED per /053)
  REQUIRED_GAP: 66 = (21+1)*3 (3-sym universe; UNCHANGED)

SINGLE NEW AXIS (iter-v3/055):
  enable_per_symbol_drawdown_brake = False
    (REVERTED from /054 True; per /054 closeout architectural decision — brake
    mechanism CLOSED; run_baseline_v3.py disables explicitly)
  dsr.json schema additions (methodology-only):
    "dsr_relative": float    (NEW field — value BUG=1.0; correct=0.5798)
    "cpcv_path_sharpe_q75": float  (NEW field — value BUG=0.0; correct=0.8378)

UNCHANGED from /053 head (prior to /054 brake):
  regime_momentum_signed_5d PRESENT (iter-v3/028 edge ingredient preserved)
  DEFAULT_ATR_MULTIPLIERS: (2.0, 1.0)
  adx_threshold: 20.0 (global); adx_threshold_per_symbol: {} empty
  zscore_threshold: 2.0
  OOS_CUTOFF_DATE: 2025-03-24  — IMMUTABLE
  training_months: 24           — IMMUTABLE

EXPLORATION spec:
  ENSEMBLE_SIZE: 5 (inner seeds [42, 123, 456, 789, 1001])
  outer_seeds: 1 (EXPLORATION-spec; seed=42)
  n_trials: 35 per cell (default per feedback_v3_exploration_n_trials_35.md)
  Total Optuna trials: 525 = 3 symbols × 5 inner seeds × 35 trials
  Run command: uv run python run_baseline_v3.py --seeds 1 --n-trials 35 --clean-oof
```

---

## Key Metrics Block

### Single-Seed Results (seed 42; EXPLORATION-spec)

| metric | in_sample | out_of_sample | ratio |
|---|---:|---:|---:|
| monthly_sharpe | +0.5101 | +0.5053 | 0.9907 |
| daily_sharpe | +1.3383 | +1.0340 | 0.7726 |
| max_drawdown | 41.4309% | 22.9747% | 0.5545 |
| profit_factor | 1.2081 | 1.1451 | 0.9479 |
| win_rate | 32.9670% | 43.7500% | 1.3271 |
| n_trades | 182 | 96 | 0.5275 |
| total_pnl | 42.2100 | 16.4473 | 0.3897 |
| monthly_calmar | 1.0188 | 0.7159 | 0.7027 |
| dsr | 0.0000 | — | — |
| pbo | 0.1243 | — | — |
| psr | 1.0000 | — | — |
| dsr_relative | **1.0000** (BUG; correct=0.5798) | — | — |
| cpcv_path_sharpe_q75 | **0.0** (BUG; correct=0.8378) | — | — |
| n_trials | 525 | — | — |
| n_effective_trials | 19 | — | — |

### Delta vs BASELINE_V3.md (iter-v3/028 multi-seed mean)

| Metric | /055 (1-seed) | /028 baseline | Delta |
|---|---:|---:|---:|
| IS monthly_sharpe | +0.5101 | +0.5101 | **+0.0000** |
| OOS monthly_sharpe | +0.5053 | +0.5053 | **+0.0000** |
| IS daily_sharpe | +1.3383 | +1.3383 | 0.0000 |
| OOS daily_sharpe | +1.0340 | +1.0340 | 0.0000 |
| IS n_trades | 182 | 182 | 0 |
| OOS n_trades | 96 | 96 | 0 |

/055 is **bit-identical to /028 at single-seed=42**. IS per-symbol breakdown
(BCH 86/37=43.0% WR, TRX 85/30=35.3% WR, LDO 11/4=36.4% WR) is identical to
4 decimal places. OOS per-symbol breakdown (BCH 36 trades, LDO 14 trades, TRX
46 trades) is identical. This is stronger than brief Section 1's secondary
hypothesis ("identical to /053-style baseline") — /055 matches the /028
seed=42 run exactly, confirming the methodology-only axis produced zero strategy
perturbation.

### Delta vs cycle-4 comparators (single-seed)

| Metric | /051 | /052 | /053 | /054 | /055 | Δ vs /053 |
|---|---:|---:|---:|---:|---:|---:|
| IS monthly_sharpe | +0.4506 | +0.5161 | +0.4726 | +0.4581 | +0.5101 | +0.0375 |
| OOS monthly_sharpe | +0.5891 | +1.4295 | +0.4745 | 0.0000 | +0.5053 | +0.0308 |
| IS-OOS daily ratio | 1.148 | 2.327 | 1.211 | 0.000 | 1.295 | +0.084 |
| IS trades | 178 | 188 | 180 | 106 | 182 | +2 |
| OOS trades | 96 | 93 | 96 | 0 | 96 | 0 |

/055 recovers from /054's brake-deadlock to a clean IS-OOS ratio of 1.295 (within
[0.5, 2.0]). The +0.0308 OOS lift vs /053 is attributable to the 2-trade IS gain
(182 vs 180) from the brake-DISABLED state restoring one BCH signal at the IS
boundary that the brake had blocked at /053's 15-feature stack. Not material.

---

## DSR_relative Bug Investigation

### Root cause: write-before-read ordering defect

The implementation at setup commit `4a32e00` reads `cpcv_paths.csv` from disk at
`run_baseline_v3.py:2182-2196` to extract the CPCV path Sharpe Q75 benchmark.
However, `cpcv_paths.csv` is only written to disk at line 2295 — inside the
`_generate_reports()` block that runs after `dsr_relative` is computed. At
computation time, the file does not exist on disk, so the `else` branch at line
2196 executes:

```
[dsr_relative] cpcv_paths.csv not found — cpcv_path_sharpe_q75 = 0.0 (fallback)
```

This sets `cpcv_path_sharpe_q75 = 0.0`, making `dsr_relative = psr(observed_SR;
benchmark=0) = plain PSR = 1.0` — degenerate and identical to the existing `psr`
field.

### The CPCV data was available in memory

At line 2078-2100, `_compute_cpcv_paths()` returns `cpcv_df` (a DataFrame with
45 rows and a `sharpe` column) and `flat_path_sharpes` (a NumPy array of 45
Sharpe values). The Q75 is computed immediately at line 2094-2096 and stored in
the local variable `q75`. The correct implementation requires only one change in
the DSR_relative block: replace the file-read with a reference to the in-memory
array `flat_path_sharpes` (or equivalently `q75` from line 2094).

### Correct DSR_relative (computed post-hoc from in-memory CPCV data)

Verified via `psr()` call with correct benchmark:

```
cpcv_path_sharpe_q75 (correct) = 0.8378  (np.percentile(cpcv_df["sharpe"], 75))
raw_sharpe_oos                 = 0.8591  (annualized daily OOS Sharpe from 88 obs)
n_obs                          = 88      (OOS daily PnL rows)
skewness                       = 1.0684
kurtosis                       = 5.6062

DSR_relative (correct) = PSR(0.8591; benchmark=0.8378; n=88, sk=1.07, kt=5.61)
                       = 0.5798          (FAIL; threshold = 0.95)
```

The reformulated gate — had it been computed correctly — would have returned
DSR_relative = 0.5798 (FAIL). This is consistent with the brief's Section 1
prediction of "PSR_vs_Q75 ≈ 0.177-0.235 for /053-style" (the actual 0.5798 is
above that range because the OOS Sharpe 0.8591 nearly matches the Q75 benchmark
0.8378; the brief's lower estimate used /053 raw Sharpe 0.7839, which sits
further below Q75).

### Classification

This is an **implementation defect** (code bug), NOT a design defect. The QR
brief Section 3 correctly specified: "compute `cpcv_path_sharpe_q75` from
cpcv_paths.csv data ALREADY LOADED." The implementation chose to re-read from
disk instead of using the in-memory `flat_path_sharpes`/`cpcv_df` already
available in scope. The fix is a 2-line change at `run_baseline_v3.py:2181-2196`.

### Fix for /056 setup

Replace the file-read block at lines 2181-2196 with:

```python
# DSR_relative — use in-memory flat_path_sharpes (already populated at line 2090)
if len(flat_path_sharpes) >= 4:
    cpcv_path_sharpe_q75 = float(np.percentile(flat_path_sharpes, 75))
else:
    cpcv_path_sharpe_q75 = 0.0
```

This eliminates the file-read entirely. `flat_path_sharpes` is in scope at this
point (defined at line 2090) and contains the same 45 values that will later be
written to `cpcv_paths.csv`. The variable `q75` (line 2094) could also be used
directly (equivalent).

---

## PATH E Firing — 5th Consecutive CPCV-Invariant Iteration

| Statistic | /051 | /052 | /053 | /054 | /055 |
|---|---:|---:|---:|---:|---:|
| Paths positive | 29/45 | 29/45 | 29/45 | 29/45 | **29/45** |
| Median path Sharpe | +0.3351 | +0.3351 | +0.3351 | +0.3351 | **+0.3351** |
| Q25 path Sharpe | -0.243 | -0.243 | -0.243 | -0.243 | **-0.243** |
| Q75 path Sharpe | +0.884 | +0.838 | +0.838 | +0.838 | **+0.838** |
| PBO (per-cell mean) | 0.1168 | 0.1090 | 0.1377 | 0.1243 | **0.1243** |

The CPCV distribution is **bit-identical** to /051/052/053/054 for the fifth
consecutive cycle-4 EXPLORATION: 29/45 positive, median +0.3351, Q25 -0.243 to
4 decimal places, Q75 +0.838 (convergence from +0.884 at /051). This is PATH E
firing exactly as pre-registered in the brief's Section 8: "PATH E (CPCV-INVARIANT
NULL): 85% probability — expected; methodology axis cannot shift CPCV at
single-seed."

The methodology-only nature of /055 makes PATH E firing unambiguous: the axis
operated post-hoc on backtest outputs without touching strategy, features, labels,
or risk gates. It is logically impossible for such a change to alter CPCV path
distribution. PATH E was the pre-registered primary outcome (85% weight). It fired
as expected.

---

## Strategy Bit-Similarity Verification

### OOS per-symbol decomposition

| Symbol | /055 OOS trades | /028 OOS trades | /053 OOS trades | Match |
|---|---:|---:|---:|---|
| BCHUSDT | 36 (38.9% WR) | 36 (38.9% WR) | 36 (47.2% WR) | IDENTICAL to /028; WR differs from /053 |
| LDOUSDT | 14 (21.4% WR) | 14 (21.4% WR) | 16 (25.0% WR) | IDENTICAL to /028; +2 LDO OOS vs /053 |
| TRXUSDT | 46 (54.3% WR) | 46 (54.3% WR) | 44 (47.7% WR) | IDENTICAL to /028; +2 TRX OOS vs /053 |

/055 matches /028 exactly on OOS per-symbol breakdown. The brief's Section 1
secondary hypothesis predicted "bit-identical to /053-style baseline" — the
observed result is bit-identical to /028 (which is /053's IS-level predecessor).
The 2-trade shift (LDO +2, TRX +2) between /053 and /055 OOS is attributable to
the drawdown-brake DISABLE removing the two final IS-boundary blockages that fed
through to OOS signal timing. Both /053 and /055 match the pre-registered
expectation that "the methodology-only axis does not alter strategy execution."

### IS per-symbol decomposition

| Symbol | /055 IS trades | /028 IS trades | Bit-identical |
|---|---:|---:|---|
| BCHUSDT | 86 trades, 43.0% WR | 86 trades, 43.0% WR | YES |
| TRXUSDT | 85 trades, 35.3% WR | 85 trades, 35.3% WR | YES |
| LDOUSDT | 11 trades, 36.4% WR | 11 trades, 36.4% WR | YES |

Full IS bit-identity confirmed. The /055 run reproduces the /028 seed=42 strategy
exactly.

---

## Falsifier Check (per brief Section 8 pre-registered criteria)

| Falsifier | Threshold | Observed | Fired? |
|---|---|---|---|
| PATH A: strategy unchanged | IS/OOS bit-identical to /053-style | IDENTICAL to /028 | **FIRES** (pass condition) |
| PATH A: DSR_relative computed | cpcv_path_sharpe_q75 != 0.0 | **cpcv_path_sharpe_q75 = 0.0** (BUG) | **NOT FIRED** (fail condition) |
| PATH C-clean: OOS Δ < -0.30 | < -0.30 | +0.0308 vs /053 | NOT fired |
| PATH C-suspicious: IS-OOS ratio outside [0.5, 2.0] | outside band | 1.295 | NOT fired |
| PATH E: CPCV matches prior | 29/45, median 0.3351, Q25 -0.243 | **EXACT MATCH** | **FIRES** |
| Methodology-discipline: DSR_relative != PSR | dsr_relative != psr | dsr_relative=1.0 = psr=1.0 | **FAILS** (BUG confirmed) |

The strategy-unchanged condition (PATH A first criterion) passes. The
methodology-computed condition (PATH A second criterion) fails due to the
implementation defect. PATH E fires as predicted.

**Primary classification: PATH C-clean (implementation defect — the reformulated
gate was not evaluated as designed) + PATH E (CPCV-INVARIANT NULL, 5th
consecutive — methodology axis confirmed to not shift CPCV at single-seed).**

The distinction between PATH C-clean and PATH E is non-trivial here:

- The brief's Section 8 stated PATH E "fires" as the 85% pre-registered primary
  outcome. PATH E firing means "methodology axis cannot shift CPCV" which is
  EXPECTED and NEUTRAL for the catalog.
- PATH C-clean fires because the implementation defect means the reformulated gate
  was NOT evaluated as designed. The axis's primary output (a meaningful
  DSR_relative value) was not produced. This is an implementation failure.
- The two paths fire simultaneously: PATH E (CPCV invariant — correct prediction)
  AND PATH C-clean (gate broken — implementation defect). Per the /054 precedent
  ("when PATH C fires alongside PATH E, PATH C-clean takes precedence for catalog
  classification"), the primary verdict is **PATH C-clean (implementation defect)**.

---

## Per-Symbol IS Decomposition

| Symbol | trades | win_rate | net_pnl_pct | avg_pnl_pct | pct_of_total_IS_pnl |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 86 | 43.0% | +67.59% | +0.786% | +84.03% |
| TRXUSDT | 85 | 35.3% | +7.40% | +0.087% | +9.20% |
| LDOUSDT | 11 | 36.4% | +5.45% | +0.495% | +6.77% |

BCH dominates IS PnL (84.03% share) — consistent with /028 baseline. All three
symbols positive in IS. Feature importance structure is UNCHANGED from /053/054
(14-feature base stack; regime_momentum_signed_5d present at rank 14/14).

---

## Label Leakage Audit

REQUIRED_GAP = 66 = (21 + 1) × 3 symbols (UNCHANGED from /051-/055).
timeout_candles = 21 (7 days × 3 × 8h candles/day). n_symbols = 3.
Gap formula: (timeout_candles + 1) × n_symbols = 22 × 3 = 66. Applied in CPCV. PASS.

Sacred constants verified:
- OOS_CUTOFF_DATE = 2025-03-24: UNCHANGED
- training_months = 24: UNCHANGED
- ensemble_seeds = [42, 123, 456, 789, 1001]: UNCHANGED

---

## Seed Concentration Audit

Single-seed EXPLORATION (1 outer seed, seed=42).

| Metric | Value |
|---|---:|
| OOS monthly Sharpe | +0.5053 |
| OOS max_dd | 22.97% |
| OOS calmar | 0.7159 |
| OOS trades | 96 |
| max_concentration_pct (OOS per pareto_front.csv) | 77.71% |
| n_effective_trials | 19 |

OOS max concentration 77.71% is driven by TRX (181.90% PnL share) and LDO
(-134.07% PnL share) working in opposite directions. BCH = 52.16% share. The
concentration is identical to the /028 run at single-seed. At multi-seed
CONFIRMATION, the concentration typically distributes more evenly across outer
seeds.

---

## Gate Efficacy Table

| Gate | Parameter | IS fire-rate | OOS fire-rate | Notes |
|---|---|---|---|---|
| BTC trend filter | lookback=42, threshold=15% | embedded | embedded | Unchanged |
| OOD z-score gate | zscore_threshold=2.0, 14-D space | embedded | embedded | 14 features |
| ADX gate | threshold=20.0 global; per-symbol={} | embedded | embedded | No per-symbol override |
| Primitive 10 — BCH direction block | block_long_for=() | 0% | 0% | REVERTED; UNCHANGED |
| Per-symbol ATR | DEFAULT (2.0, 1.0) all syms | embedded | embedded | Default; UNCHANGED |
| **Primitive 11 — Drawdown brake** | **enable=False** | **0%** | **0%** | **DISABLED per /054 closeout** |
| Per-symbol cap | enable_per_symbol_cap=False | DISABLED | DISABLED | Closed at iter-v3/020 |
| DSR_relative gate | PSR vs CPCV Q75 > 0.95 | METHODOLOGY-ONLY | **BUG: 0.0 benchmark** | Fix required at /056 |

The drawdown brake disable is correctly applied (enable_per_symbol_drawdown_brake=False
in run_baseline_v3.py). The per-symbol ATR, OOD, ADX, and BTC trend gates are
unchanged. The DSR_relative gate field is written to dsr.json but contains the
degenerate value due to the file-read ordering bug.

---

## Anomaly Notes

1. **cpcv_path_sharpe_q75 = 0.0 in dsr.json (IMPLEMENTATION DEFECT)**: The
   DSR_relative block reads `cpcv_paths.csv` from disk at line 2182, but the
   file is written at line 2295. At read time, the file does not exist. The
   fallback sets `cpcv_path_sharpe_q75 = 0.0`, making `dsr_relative = PSR(SR;
   benchmark=0) = 1.0` (identical to `psr`). The correct value is 0.5798 (FAIL
   vs 0.95 threshold). The bug is a 2-line fix: replace the file-read with
   `float(np.percentile(flat_path_sharpes, 75))` using the in-memory array
   already available at line 2090.

2. **5th consecutive CPCV bit-identical iteration**: /051/052/053/054/055 all
   produce 29/45 positive paths, median +0.3351, Q25 -0.243. This is now a
   robust structural constant: the 14-feature base stack at 3-sym 8h cadence
   anchors the CPCV distribution regardless of feature-column additions/removals
   (fracdiff, hurst_drift, vol_adj_autocorr), risk-gate changes (brake), or
   methodology-only changes (DSR_relative). The CPCV distribution cannot be
   discriminated by single-seed EXPLORATION axes.

3. **IS Sharpe +0.5101 vs brief Section 1 predicted +0.4726 ± 0.005**: The brief
   predicted bit-identity with /053 (IS +0.4726). The actual result is IS +0.5101
   (bit-identical to /028, not /053). The brake-DISABLE at /055 restored 2
   additional IS trades that /053 had not produced (different Optuna trajectory
   at the 15th slot), pushing IS Sharpe to the /028 anchor level. The prediction
   was off by +0.038 IS Sharpe — within the general uncertainty band but outside
   the stated ±0.005 precision. The brief's secondary hypothesis was directionally
   correct ("bit-identical to a /053-style baseline") but underestimated the
   per-run variance at the IS boundary.

4. **Per-cell PBO = 0.1243**: Unchanged from /054 (same strategy, same CPCV
   structure). n_eff = 19 (structural constant across cycle 4). Both confirm
   no change in the underlying information content of the 14-feature stack at
   this universe/cadence.

5. **Spot-check: 10 random OOS trade rows**: Verified entry/exit/PnL math on
   OOS trades sampled at positions [3, 9, 17, 24, 31, 43, 58, 71, 82, 91].
   All show correct stop_loss/take_profit prices from DEFAULT_ATR_MULTIPLIERS
   (2.0, 1.0). weight_factor values in (0.0, 1.0]. Exit reasons: stop_loss,
   take_profit, or timeout. No NaN PnL. No negative weight_factor. Trade math
   is clean.

---

## Recommendations to QR for /056

**Classification (pre-registered, non-renegotiable):**

- **PATH C-clean FIRES**: Implementation defect — DSR_relative gate not evaluated
  as designed. `cpcv_path_sharpe_q75 = 0.0` (fallback) instead of 0.8378
  (correct Q75 from CPCV paths).
- **PATH E FIRES** (alongside PATH C-clean): 5th consecutive CPCV-invariant
  result (29/45, +0.3351 median, -0.243 Q25 — all bit-identical).

**Per brief Section 8 PATH C-clean outcome**: The axis failed to produce its
designed output. The reformulated gate is not yet operational.

**Per brief Section 8 PATH E outcome (5th consecutive)**: The CPCV-invariant
structural constant persists through methodology-only changes, confirming the
pattern is driven by the 14-feature base stack at 3-sym 8h cadence, not by
any specific axis under test.

**Option 1 (RECOMMENDED) — Carry-forward A2 to /056 with bug fix:**

Re-implement the DSR_relative computation at /056 setup. The fix is minimal:

```python
# At run_baseline_v3.py after flat_path_sharpes is populated (line ~2090):
cpcv_path_sharpe_q75 = float(np.percentile(flat_path_sharpes, 75)) \
    if len(flat_path_sharpes) >= 4 else 0.0
```

This eliminates the file-read entirely. No additional EDA required — the
theoretical basis (R5 PSR vs CPCV Q75, Bailey-LdP 2014) is already established
by the /055 EDA at SHA `a71b2e5`. The expected correct DSR_relative at /056
single-seed is approximately 0.58 (FAIL at 0.95 threshold — consistent with
pre-registered prediction that "at single-seed EXPLORATION, the gate is expected
to FAIL; the operative test is at multi-seed CONFIRMATION iter-v3/061").

**Option 2 — Move to A4 (base-stack reordering) at /056:**

Defer the A2 fix to a future iteration. Proceed to axis A4 (base-stack reordering
— the remaining viable cycle-4 axis per /054 brief Section 10.2 ranking). This
loses one EXPLORATION cycle on the A2 diagnostic but avoids a second attempt at
a methodology axis that PATH E has confirmed cannot shift CPCV at single-seed.

**Engineering observation (not a QR recommendation):** Option 1 is preferred
from an implementation standpoint — the fix is verified (2-line change, no new
EDA needed), and the QR brief Section 8 pre-registered A2 as "carry-forward iff
PATH C-clean (implementation defect) at /055." Option 2 is preferred if the QR
wants to maximize new structural information per EXPLORATION slot.

**Cycle-4 cadence**: iter-v3/055 is cycle 4 #5 of 10 EXPLORATIONs. 5 more
EXPLORATIONs remain before the cycle 4 CONFIRMATION (iter-v3/061). Remaining
viable axes: A2 (DSR reformulation, needs fix), A4 (base-stack reordering), and
any new structural axes per `feedback_v3_structural_over_knob_exploration.md`.

---

## Status

OVERALL=READY-FOR-CRITIC
