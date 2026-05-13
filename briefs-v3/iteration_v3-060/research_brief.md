# Iteration v3-060 — Research Brief (Cycle 1 EXPLORATION-MODE-REFERENCE: First 3-seed EXPLORATION-mode run + TRX OOS Diagnostic — PATH A passive)

**Type**: EXPLORATION-MODE-REFERENCE (cycle 1 #1; FIRST 3-seed EXPLORATION-mode run +
passive TRX diagnostic publication)
**Track**: v3 (rigor arm) — sixtieth iteration
**Branch**: `iteration-v3/060` (created from `iteration-v3/059` HEAD at SHA `84adfcc`;
includes Phase B-3 unified ensemble at `ab2d9ac` + walk-forward fix at `e149e9d`
+ Phase A revert at `31665f6` + mode-flag refactor at `56f5a30`)
**Date**: 2026-05-13
**Author**: QR (EDA-driven per `feedback_v3_axis_selection_quant_discipline.md`)
**EDA SHA**: `6ab47b4` — `analysis/iteration_v3-060/trx_diagnostic.py`

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE             = 2025-03-24    # IMMUTABLE
training_months             = 24             # IMMUTABLE
EXPLORATION_ENSEMBLE_SIZE   = 3              # active for /060 (--exploration flag)
CONFIRMATION_ENSEMBLE_SIZE  = 10             # default; reserved for cycle 1 CONFIRMATION
ENSEMBLE_SEEDS              = (191664963, 1662057957, 1405681631, 942484272, 929893137,
                                33158374, 1465339467, 1273345680, 115579757, 1952249162)
ACTIVE_SEEDS (/060)         = ENSEMBLE_SEEDS[0:3] = (191664963, 1662057957, 1405681631)
n_trials                    = 35             # EXPLORATION default (per feedback_v3_exploration_n_trials_35.md)
colsample_bytree            = Optuna-tuned   # NOT hardcoded 1.0
OOS_CUTOFF_MS               = 1742774400000
```

**IS window (24 months)**: 2023-03-24 00:00 UTC through 2025-03-23 23:59 UTC
**OOS window**: 2025-03-24 00:00 UTC onward

Sacred constants UNCHANGED. The QR sees iter-v3/060 OOS metrics for the FIRST time in Phase 7.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION-MODE-REFERENCE (cycle 1 #1; FIRST 3-seed EXPLORATION-mode run
  + passive TRX diagnostic publication)
  - First post-RE-ANCHOR #2 cycle 1 EXPLORATION
  - First post-mode-flag-refactor (SHA 56f5a30) EXPLORATION-mode run in v3 history
  - Anchor (informational): BASELINE_V3.md iter-v3/059 unified 10-seed CONFIRMATION-mode
    (IS +1.0894 / OOS +0.5791). /060 is NOT bit-identical to /059 — /059 ran at
    ENSEMBLE_SIZE=10; /060 runs at ENSEMBLE_SIZE=3 (EXPLORATION mode).
  - /060 establishes the EXPLORATION-mode reference baseline for cycle 1
    single-axis EXPLORATIONs (iter-v3/061-068) to compare against.
  - Wall-clock target: 2h EXPLORATION cap
  - Run command: uv run python run_baseline_v3.py --exploration --seeds 1 --n-trials 35

Phase chain leading to this iteration:
  Phase B-3 (commit ab2d9ac): unified ensemble (outer-seed loop eliminated;
    single inference path)
  Phase A Optuna n_jobs=2 ATTEMPTED at `0a3c30e`, REVERTED at `31665f6` due to
    5x GIL slowdown; current state n_jobs=1.
  Walk-forward fix (commit e149e9d): 22-candle embargo at train/test boundary
  RE-ANCHOR #2 setup (commit 20095a8): ITERATION_LABEL="v3-059"; brief + phase5p5 gate
  RE-ANCHOR #2 backtest (HEAD 31665f6): produced iter-v3/059 numbers (10-seed
    CONFIRMATION-mode)
  BASELINE_V3.md RE-ANCHOR #2 update (commit 84adfcc): canonical anchor
  Mode-flag refactor at SHA 56f5a30 (--exploration → ENSEMBLE_SIZE=3
    ENSEMBLE_SEEDS[0:3]; CONFIRMATION default ENSEMBLE_SIZE=10 unchanged).
    User directive 2026-05-13 mid-setup: 10 seeds = CONFIRMATION-only.
```

Brief Section 0.5 commit chain wording cleaned per Critic FINAL `0fc18c2`
Recommendation #4: prior `briefs-v3/iteration_v3-059/research_brief.md` Section 0.5
Stage 3 referenced "Optuna n_jobs=2 (Phase A commit `0a3c30e`)" without acknowledging
the `31665f6` revert. This brief explicitly documents current state n_jobs=1.

---

## Section 1 — Hypothesis

### Path A (Passive Diagnostic) at EXPLORATION mode — chosen per Section 10 EDA findings

**HYPOTHESIS**: Under EXPLORATION mode (ENSEMBLE_SIZE=3, ENSEMBLE_SEEDS[0:3]), the
/028 bundle reproduces a 3-seed-mode reference baseline. The TRX diagnostic findings
from `analysis/iteration_v3-060/trx_diagnostic.py` are published as cycle 1 #1 axis
groundwork; no code change is made beyond invoking `--exploration`. iter-v3/060
establishes the EXPLORATION-mode anchor that subsequent cycle 1 single-axis
EXPLORATIONs (iter-v3/061-068) will compare against.

**Mechanism (passive at 3-seed)**: iter-v3/060 invokes `run_baseline_v3.py
--exploration` (no code change other than the mode flag itself). The active seed
slice is ENSEMBLE_SEEDS[0:3]; the per-seed/per-month Optuna train + 3-seed
soft-vote remains the same machinery as /059, just averaged across 3 inner seeds
instead of 10. **The /060 backtest WILL produce DIFFERENT numbers from /059**
because 3-seed averaging has higher variance than 10-seed averaging — this is
the intentional outcome that establishes the EXPLORATION-mode reference for cycle 1.

**What this iteration tests**: (a) the new EXPLORATION-mode plumbing produces a
coherent baseline at 3 seeds; (b) the /028 bundle (BASELINE_V3.md-anchored)
retains positive IS+OOS Sharpe at 3-seed averaging; (c) the TRX diagnostic
Q1-Q7 findings are validated as the cycle 1 #1 axis-feeding insights for
iter-v3/061+ axis selection.

**What this iteration does NOT test**:
- Any feature SWAP, addition, or removal
- Any risk primitive change
- Any labeling change
- Any universe change
- Bit-identity with /059 (architecturally impossible — different ensemble size)

---

## Section 2 — IS-Only Numerical Evidence (committed EDA at `6ab47b4`)

Analysis script: `analysis/iteration_v3-060/trx_diagnostic.py`
Output directory: `analysis/iteration_v3-060/`
Run command: `uv run python analysis/iteration_v3-060/trx_diagnostic.py`

### Section 2.1 — Q1: TRX feature importance vs BCH/LDO (last-month IS model)

| Scope | top1 feature | top1 share % | top3 share % |
|---|---|---:|---:|
| BCHUSDT | max_dd_window_50 | 10.12 | 29.63 |
| LDOUSDT | ret_skew_200 | 9.06 | 25.64 |
| **TRXUSDT** | range_realized_vol_50 | **9.58** | **27.75** |
| portfolio | ret_skew_200 | 8.82 | 25.82 |

**Reading**: TRX top-3 importance share (27.75%) is INDISTINGUISHABLE from BCH (29.63%)
and LDO (25.64%). The model is NOT under-weighting TRX features. **Path B
(TRX-specific feature engineering) is NOT supported by this evidence** — feature
importance distribution shows no representation gap.

### Section 2.2 — Q2: TRX label distribution per quarter (IS only)

| Quarter | n_trades | long_share | sl_share | win_rate | weighted_pnl |
|---|---:|---:|---:|---:|---:|
| 2022Q1 | 5 | 0.00 | 0.60 | 0.20 | -1.39 |
| 2022Q4 | 3 | 0.67 | 0.00 | 0.67 | +6.16 |
| **2023Q1** | **12** | **0.00** | **0.75** | **0.17** | **-10.74** |
| **2023Q4** | **15** | **0.80** | **0.80** | **0.20** | **-6.55** |
| 2024Q1 | 11 | 0.55 | 0.82 | 0.18 | -6.72 |
| 2024Q3 | 9 | 0.78 | 0.56 | 0.22 | +0.16 |
| 2024Q4 | 11 | 0.27 | 0.73 | 0.18 | +0.12 |
| 2025Q1 | 3 | 0.67 | 0.00 | 0.67 | +5.02 |

**Reading**: TRX exhibits temporal regime-skew (2023-Q1: 12 SHORTs, 0 LONGs, all
losing; 2023-Q4: 12 LONGs + 3 SHORTs, mostly losing). The model captures direction
but not edge — WR collapses to 17-22% in 2023-Q1 / 2023-Q4 / 2024-Q1, the longest
losing streaks. **The labels are taking direction, but the SL-floor hit rate (0.73-0.82
in losing quarters) shows the entries are systematically wrong.**

### Section 2.3 — Q3: TRX trade PnL concentration (top-K cumulative share)

| split | n_trades | total_weighted_pnl | top1 share % | **top3 share %** | top5 share % | top10 share % | killed_pct |
|---|---:|---:|---:|---:|---:|---:|---:|
| **IS** | 79 | **-7.35** | -93.86 | -232.26 | -332.83 | -522.93 | 18.99% |
| **OOS** | 48 | **+4.16** | **91.48** | **265.36** | 389.68 | 627.83 | 6.25% |

**Reading — DECISIVE finding**: TRX OOS weighted_pnl=+4.16 is a single-trade
outcome. The top-1 OOS trade contributes 91.5% of total OOS weighted_pnl; the
top-3 contribute 265% (the surplus over 100% means TRX's top-3 winners exceed
the total — i.e., other trades are losing money that cancels most of the wins).
**The +4.16 is statistically equivalent to noise** at trade-level granularity.

Critical: 18.99% of TRX IS trades were vol-scaling-killed (weight_factor=0). On
the IS side, TRX total weighted_pnl is **NEGATIVE -7.35**, contradicting the
comparison.csv `pct_of_total_pnl=3.47%` (which uses unweighted net_pnl_pct). The
BASELINE_V3.md narrative "TRX IS 3.47% of IS PnL" is misleading on a portfolio
weighted basis (TRX is actually -9.4% of portfolio IS weighted_pnl — a net DRAG).
See Q7 below.

### Section 2.4 — Q4: TRX vs BCH vs LDO feature scale divergence (top-5 only)

| feature | TRX mean | BCH mean | LDO mean | TRX vs BCH meanZ | std_ratio max/min |
|---|---:|---:|---:|---:|---:|
| ret_kurt_200 | **10.10** | 5.23 | 3.75 | 0.62 | 5.94 |
| max_dd_window_50 | -0.17 | -0.22 | -0.26 | 0.46 | 1.25 |
| range_realized_vol_50 | 0.024 | 0.030 | 0.036 | 0.45 | 1.36 |
| ema_spread_atr_20 | 0.29 | -0.09 | -0.24 | 0.28 | 1.10 |
| hurst_100 | 0.997 | 1.011 | 1.001 | 0.27 | 1.21 |

**Reading**: TRX has materially higher kurtosis (`ret_kurt_200` mean 10.10 vs BCH
5.23, 1.94× higher; std 16.94 vs 3.86, 4.4× higher). Otherwise feature scales are
mostly within Z=0.5 — model can normalize. **`ret_kurt_200` scale divergence is
the only material feature-level anomaly**, but Z=0.62 is moderate. Path B would
not be justified by feature engineering alone — the issue is signal-quality,
not feature-representation.

### Section 2.5 — Q5: TRX trade outcome by ATR regime (IS-window terciles)

| split | atr_regime | n_trades | win_rate | weighted_pnl | avg_per_trade |
|---|---|---:|---:|---:|---:|
| IS | mid | 33 | 0.273 | -1.94 | -0.059 |
| IS | high | 46 | 0.239 | -5.42 | -0.118 |
| OOS | mid | 20 | 0.450 | +1.68 | +0.084 |
| OOS | high | 28 | 0.357 | +2.48 | +0.089 |

**Reading**: TRX trades concentrate exclusively in `mid` and `high` ATR regimes
(low-vol regime is filtered out by RiskV2 vol-scaling). IS WR is 24-27% across
regimes (both negative); OOS WR is 36-45% (both positive but small). **No
labeling-axis intervention by ATR regime alone would clearly improve outcomes** —
the issue isn't "trades in the wrong vol regime", it's that the signal is
high-variance noise.

### Section 2.6 — Q6: /058 seed42 vs /059 unified roster overlap

| metric | value | weighted_pnl |
|---|---:|---:|
| /058 seed42 total | 54 trades | +23.03 |
| /059 unified total | 48 trades | +4.16 |
| **intersection (same open_time + direction)** | **40 trades** | (shared) |
| **only in /058 (consensus-dropped from /059)** | **14 trades** | **+13.92** |
| only in /059 (consensus-added vs /058) | 8 trades | -5.17 |

**Reading**: The architecture flip dropped 14 trades from /058's roster carrying
+13.92 PnL, and added 8 new trades carrying -5.17 PnL. The dropped trades
explain 73.6% of TRX's /058 → /059 weighted_pnl collapse (-18.87 total: -13.92
from dropped + -5.17 from added = -19.09 vs observed -18.87, residual is overlap
PnL drift). **/058's TRX +23.03 was structurally seed-42-roster-dependent**; under
unified architecture this lottery does not repeat.

### Section 2.7 — Q7: RiskV2 vol-scaling effect — DECISIVE finding

| split | symbol | n_trades | unweighted_net_pnl_pct | **weighted_pnl** | weight on wins | weight on losses | **win_w − loss_w** |
|---|---|---:|---:|---:|---:|---:|---:|
| IS | BCH | 83 | +109.23 | +76.61 | 0.575 | 0.476 | **+0.099** |
| IS | LDO | 9 | +0.89 | +8.93 | 0.707 | 0.485 | **+0.222** |
| **IS** | **TRX** | **79** | **+3.95** | **-7.35** | **0.546** | **0.606** | **-0.061** |
| OOS | BCH | 34 | +26.58 | +24.75 | 0.722 | 0.650 | +0.072 |
| OOS | LDO | 12 | -14.46 | -6.18 | 0.900 | 0.711 | +0.189 |
| **OOS** | **TRX** | **48** | **+6.47** | **+4.16** | **0.650** | **0.664** | **-0.014** |

**Reading — STRUCTURAL finding**: TRX is the ONLY symbol in BCH/LDO/TRX where
RiskV2 average weight_factor on winning trades is LOWER than on losing trades, in
BOTH IS and OOS. For BCH, win_w − loss_w = +0.099 / +0.072 (Kelly-aligned: high
conviction → high weight → wins). For LDO, +0.222 / +0.189. For TRX, **-0.061 /
-0.014** — anti-correlated.

This means the RiskV2 vol-scaling z-score on the candidate signal at trade entry
is reducing weight on TRX trades that turn out to be wins. **The RiskV2 vol-scaling
is anti-Kelly on TRX** — it amplifies losses and shrinks wins.

**Critical interpretation**: TRX's "+3.95% IS net_pnl_pct" (unweighted) becomes
"-7.35 IS weighted_pnl" because vol-scaling tunes TRX's most-confident signals
DOWN and its least-confident UP. The model is producing usable signal on TRX, but
RiskV2 is misaligned with TRX's signal quality. The BASELINE_V3.md narrative
"TRX 3.47% of IS PnL" is structurally misleading; on a weighted basis, TRX is a
net IS DRAG (-9.4% of portfolio IS weighted_pnl = -7.35 / 78.18 × 100).

This is a SYSTEM-level diagnostic finding, not a TRX-feature finding. Path B
(TRX-specific feature engineering) does NOT address this. Path C (TRX-specific
label parameters) does NOT address this. A future axis (iter-v3/061+) targeting
the **RiskV2 weight_factor calibration** (not currently active in v3 anywhere
in the cycle 1 axis priorities) is the highest-value follow-up.

### Section 2.8 — Synthesis: Path decision

| Path | Evidence For | Evidence Against | Decision |
|---|---|---|---|
| **A — Passive diagnostic** | All 7 EDA questions point to system-level issue (Q7 RiskV2 anti-Kelly), not TRX-feature issue. iter-v3/060 should preserve /059 baseline numbers and feed EDA into iter-v3/061+ axis selection. | NULL-RESULT classification is mandatory under bit-identical backtest. | **CHOSEN** |
| B — TRX feature engineering | Q4 shows ret_kurt_200 scale divergence (Z=0.62). | Q1 shows TRX feature importance share = BCH/LDO. Q3 shows OOS +4.16 is single-trade lucky-tail (no feature can fix lottery). | NO |
| C — TRX label parameter customization | Q2 shows temporal regime skew in TRX labels. | Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`: per-symbol customizations lift OOS but break IS aggregate at multi-seed. TRX IS is already -7.35 weighted; per-symbol relabeling would not fix the Q7 vol-scaling anti-Kelly issue. | NO |
| D — Drop TRX universe contraction | Q3 + Q7 strongly suggest TRX is net DRAG on portfolio weighted_pnl. | Per `feedback_insist_on_symbols.md`: "Single Gate 3 fail is a signal to investigate, not to reject"; lookback-sensitivity + alt-labeling not yet run. Cannot propose Path D from one EDA cycle. iter-v3/061-068 should run lookback-sensitivity + alt-labeling under Path A's diagnostic guidance before considering universe contraction. | **DEFERRED** to iter-v3/065+ pending further evidence |

**Path A chosen at EXPLORATION mode.** iter-v3/060 backtest invokes `--exploration`
(ENSEMBLE_SIZE=3, ENSEMBLE_SEEDS[0:3]); no other V3 code state change. The output
numbers will diverge from /059's 10-seed CONFIRMATION-mode anchor by construction
(3-seed vs 10-seed averaging). Use the EDA to inform iter-v3/061+ axis selection —
primary recommendation: **investigate RiskV2 vol-scaling weight_factor calibration
as iter-v3/061 candidate axis** (secondary to DSR_relative recalibration per
Critic Rec #1).

### Section 2.10 — EXPLORATION-mode reference scope

The TRX diagnostic Q1-Q7 are the cycle 1 #1 publishable EDA. The /060 backtest
itself is the **EXPLORATION-mode reference run** (3 seeds; first of cycle 1) —
its headline numbers (IS Sharpe, OOS Sharpe, BCH/LDO/TRX weighted_pnl) become the
EXPLORATION-mode anchor for iter-v3/061-068 cycle 1 EXPLORATIONs to compare
against (anchor delta ≥ +0.10 IS Sharpe to be classified PROMISING; per the
standard cycle 1 axis-classification taxonomy).

Subsequent cycle 1 single-axis EXPLORATIONs MUST anchor against /060's 3-seed
numbers, NOT /059's 10-seed numbers. The /059 anchor remains the
CONFIRMATION-mode reference (for iter-v3/069 cycle 1 CONFIRMATION re-anchoring,
and for cross-cycle BASELINE_V3.md comparisons), but EXPLORATION-mode
axis-attribution at /061-068 uses /060 numbers as its denominator.

---

## Section 3 — Proposed Changes (Setup Commit Locked)

### Edit 1: `run_baseline_v3.py` — ITERATION_LABEL only (already at SHA 2d82079)

```python
ITERATION_LABEL = "v3-060"
```

### Edit 2: Mode flag (committed at SHA `56f5a30`)

```
--exploration  → ensemble_size_for_run = EXPLORATION_ENSEMBLE_SIZE = 3
                 active_ensemble_seeds  = ENSEMBLE_SEEDS[0:3]
                                        = (191664963, 1662057957, 1405681631)
```

Path A passive at EXPLORATION mode. ONE substantive change: invoke
`run_baseline_v3.py` with `--exploration` (ENSEMBLE_SIZE=3 derived;
ENSEMBLE_SEEDS[0:3] active). No code change to V3_FEATURE_COLUMNS,
V3_LABEL_PARAMS, or universe. **The mode flag itself is the iteration's
substantive intervention vs /059.**

### Carry-forward state (all UNCHANGED from /059 source code):

- `V3_FEATURE_COLUMNS_TOP_N`: 14 features identical to /059
- `V3_MODELS = ("BCHUSDT", "LDOUSDT", "TRXUSDT")`
- `V3_ATR_MULTIPLIERS_PER_SYMBOL = {}`
- `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)`
- `RiskV2Config(adx_threshold_per_symbol={}, block_long_for=(), enable_per_symbol_drawdown_brake=False)`
- `REQUIRED_GAP = 66 = (21+1) × 3`
- `CONFIRMATION_ENSEMBLE_SIZE = 10` (default — inactive at /060)
- `EXPLORATION_ENSEMBLE_SIZE = 3` (active at /060 via --exploration)
- `ENSEMBLE_SEEDS` = 10-tuple lineage-preserving (only [0:3] active)
- Walk-forward fix at `e149e9d` present
- Optuna `n_jobs=1` (Phase A revert at `31665f6`)

**No other edits.** The setup commits are `2d82079` (brief + ITERATION_LABEL)
+ `56f5a30` (mode flag). The substantive changes are the ITERATION_LABEL bump
and the `--exploration` invocation at Phase 6 launch.

---

## Section 4 — Expected OOS Impact

### Section 4.1 — EXPLORATION-mode predictions (3-seed bands)

Under the EXPLORATION-mode architecture (ENSEMBLE_SIZE=3 vs /059's =10), iter-v3/060
WILL produce different numbers from /059 by construction. The "bit-identical to /059"
contract from the original /060 brief is INVALID. Predicted bands reflect the
higher variance of 3-seed averaging vs 10-seed averaging:

| Metric | /059 (10-seed CONFIRMATION) | /060 predicted (3-seed EXPLORATION) | Justification |
|---|---:|---:|---|
| IS Sharpe | +1.0894 | **+0.85 to +1.15** (band ±0.30) | 3-seed reduces averaging convergence; higher variance |
| OOS Sharpe | +0.5791 | **+0.30 to +0.85** (band ±0.55) | 3-seed retains lottery exposure at single-seed mode side |
| OOS/IS ratio | 0.5316 | similar **[0.35, 0.75]** | random walk; both metrics noisier at 3 seeds |
| BCH OOS weighted_pnl | +24.75 | **comparable (±20% band)** | BCH IS concentration 95.76% — direction-aligned |
| LDO OOS weighted_pnl | -6.18 | **-3 to -10** (small-trade lottery) | LDO has 12 OOS trades — variance dominates |
| TRX OOS weighted_pnl | +4.16 | **-5 to +15** | per Q3 finding (top-1 trade = 91.5% / top-3 = 265%); pure noise |
| OOS trade count | 94 | **90-110** (±20%) | confidence threshold convergence at 3 seeds slightly different from 10 |
| cpcv_frac_positive_paths | 0.6444 | **0.50 to 0.70** | architecture-independent but 3-seed run has fewer trial points feeding CPCV |
| DSR_relative | 0.1134 | **0.05 to 0.25** | informational; CPCV-Q75 benchmark unchanged |

**Falsifier**: If /060 IS Sharpe falls below +0.50 OR OOS Sharpe falls below 0.0,
the 3-seed EXPLORATION mode is structurally inadequate for cycle 1 single-axis
discrimination; user must re-evaluate (escalate to 5-seed). Per
`feedback_v3_axis_saturation_predictor.md`, predicted lower-bound floors are above
the falsifier; if the floors are hit, the iteration is auto-classified
NULL-RESULT-INFRASTRUCTURE rather than RE-ANCHOR-EXPLORATION.

### Section 4.2 — BCH IS sensitivity projection (per Critic Rec #3 mandate)

BCH carries 95.76% of IS weighted_pnl at /059 (BCH IS weighted_pnl=+76.61 vs
portfolio +78.18). At /060 (Path A passive, only mode flag changed) the prediction
is **BCH IS share remains in [85%, 100%] band**. If BCH share drops below 80%,
flag as PATH-DIVERGENCE-AT-MODE-FLAG (architectural anomaly — would indicate
that 3-seed averaging produces a materially different portfolio-IS distribution
than 10-seed averaging on the same underlying code, which would require its own
investigation).

Critic Rec #3 mandate (every cycle 1 brief Section 4 must project BCH IS impact)
is satisfied: the band [85%, 100%] is the predicted /060 BCH IS share, with
PATH-DIVERGENCE-AT-MODE-FLAG falsifier at <80%.

### Section 4.3 — Behavioral effect predictor (per `feedback_v3_axis_saturation_predictor.md`)

Per the axis saturation predictor rule: brief Section 4 must include "behavioral
effect predictor (explicit estimate of how many IS trades will change), with
falsifier triggered if observed change is below predicted lower bound."

Under EXPLORATION-mode at 3-seed: predicted IS-trade-count band = **[150, 200]**
(vs /059's 171; ±15% reflects the soft-vote consensus threshold sensitivity to
3-seed vs 10-seed averaging). Predicted OOS-trade-count band = **[80, 115]**
(vs /059's 94).

Falsifier: if trade counts fall outside the predicted bands by more than 30%,
investigate the soft-vote consensus mechanism for mode-flag interaction bugs.

### Section 4.4 — Falsifier (EXPLORATION-mode rewritten)

**Falsifier triggered if**:
- IS Sharpe < +0.50 OR
- OOS Sharpe < 0.0 OR
- BCH IS share < 80% OR
- IS trade count outside [128, 222] (±30% of /059's 171) OR
- OOS trade count outside [66, 122] (±30% of /059's 94)

If any falsifier fires, classification flips to NULL-RESULT-INFRASTRUCTURE; user
re-evaluates ENSEMBLE_SIZE for EXPLORATION (potentially raise to 5).

---

## Section 5 — Risk Mitigation

Same 7-primitive gate stack as /059 (and /028, /058):

1. BTC trend kill (threshold_pct=15.0, lookback=42 bars)
2. Vol scaling (zscore_threshold=2.0) — **CONFIRMED VIA Q7 EDA as anti-Kelly on
   TRX**; risk to investigate at iter-v3/061+
3. ADX gate (adx_threshold=20.0, adx_threshold_per_symbol={})
4. Hurst regime gate
5. Feature z-score OOD (threshold=2.0)
6. Low-vol filter
7. Hit-rate gate (DISABLED)

Per-symbol drawdown brake: DISABLED
Block-long: EMPTY

Risk surface is identical to /059 source-code state (no Path A axis change). Risk
primitives unchanged from /059. The 3-seed mode preserves the unified-architecture
risk-primitive stack identically. Per `feedback_v3_single_seed_frozen_baseline.md`,
3-seed at EXPLORATION may exhibit some non-frozen-baseline behavior vs prior
single-seed pattern but is materially MORE stable than 1-seed. The Q7 EDA finding
that RiskV2 vol-scaling is anti-Kelly on TRX is recorded here as iter-v3/061
candidate axis fodder; no /060 change is proposed.

---

## Section 6 — Risk Management Design (UNCHANGED)

8-primitive framework status (all UNCHANGED from /059):

| Primitive | Status | Threshold | EDA Q7 finding |
|---|---|---|---|
| Vol-adjusted sizing | ACTIVE | zscore_threshold=2.0 | **Anti-Kelly on TRX** (Q7) — iter-v3/061 candidate |
| ADX gate | ACTIVE | 20.0 (global); {} per-symbol | - |
| Hurst regime | ACTIVE | hurst_100 >= 0.5 | - |
| Z-score OOD | ACTIVE | zscore_threshold=2.0 | - |
| Drawdown brake | DISABLED | per_symbol=False | per-symbol drawdown brake retired at iter-v3/054 |
| BTC contagion kill | ACTIVE | threshold_pct=15.0 | - |
| Per-symbol kill switch | DISABLED | block_long_for=() | - |
| Hit-rate gate | DISABLED | enabled=False | - |

No /060 changes. The vol-scaling anti-Kelly finding for TRX is iter-v3/061 axis
candidate fodder, NOT a /060 modification.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

Under EXPLORATION-mode Path A, the failure modes shift from "bit-identity
violation" (the original contract) to "3-seed variance noise floor inadequate
for cycle 1 axis-attribution discrimination."

**Most plausible failure mode** (predicted probability ~25%):

- **3-seed variance noise floor too high**: The 3-seed EXPLORATION mode produces
  high-variance OOS at this volume (3 syms × 94 trades over 14 months OOS).
  Cycle 1 EXPLORATIONs (iter-v3/061-068) using /060 as anchor may show large
  axis-attribution noise — a +0.15 OOS Sharpe lift from a real signal may be
  indistinguishable from a +0.15 lift from 3-seed lottery.

  **Mitigation**: cycle 1 single-axis EXPLORATIONs adopt PASS criteria of
  (a) IS Sharpe shift ≥ +0.10 AND (b) OOS Sharpe shift ≥ +0.20 to clear lottery
  noise. Iterations near the noise floor classify as PROMISING-INERT pending
  CONFIRMATION-mode validation. If /060 itself falls below the Section 4.4
  falsifier thresholds (IS < +0.50 or OOS < 0.0), classification flips to
  NULL-RESULT-INFRASTRUCTURE and user re-evaluates ENSEMBLE_SIZE.

**Second most plausible failure mode** (predicted probability < 5%):

- **BCH IS concentration shifts unexpectedly under 3-seed averaging** (BCH share
  drops below 80%): would indicate that the 3-seed soft-vote drops BCH consensus
  trades disproportionately vs LDO/TRX. Action: Phase 7 PATH-DIVERGENCE-AT-MODE-FLAG
  investigation — examine per-symbol IS roster vs /059 and quantify the soft-vote
  drop pattern.

**Third most plausible failure mode** (predicted probability < 5%):

- **Backtest runtime failure**: hardware/environment issue at Phase 6. Action:
  re-run Phase 6 once after environment refresh; if persistent, debug. Does not
  affect the EXPLORATION-mode-reference establishment hypothesis.

**Predicted-success path** (probability ~65%):

- **Path A EXPLORATION-mode-reference established**: /060 numbers fall within
  predicted bands (IS [+0.85, +1.15], OOS [+0.30, +0.85]); classification: PASS
  (EXPLORATION-MODE-REFERENCE). The /060 numbers become the cycle 1 EXPLORATION
  anchor; iter-v3/061-068 compare axis deltas against /060 (NOT /059). EDA Q7
  finding feeds iter-v3/061+ axis selection (RiskV2 vol-scaling weight_factor
  calibration as primary candidate).

---

## Section 8 — LOCKED Criteria (EXPLORATION-MODE-REFERENCE discipline)

The /059 bit-identity-based criteria from the original /060 brief are INVALID
(3-seed EXPLORATION mode produces different numbers from 10-seed CONFIRMATION
mode by construction). The LOCKED criteria below replace them.

### Section 8.1 — PASS (EXPLORATION-MODE-REFERENCE established)

PASS requires ALL of:
- IS Sharpe ≥ **+0.50** (anchor floor — relaxed from 1.0 due to 3-seed variance)
- OOS Sharpe ≥ **0.0** (anchor floor — relaxed from +0.5 due to 3-seed variance)
- BCH IS share in **[80%, 100%]** band
- cpcv_frac_positive_paths ≥ **0.50** (slightly relaxed from /059's 0.55 due to fewer trial points)
- No methodology FAIL (Critic Foundation Audit + Anti-Pattern scan clean)
- `ensemble_summary.json` `mode == "exploration"` AND `ensemble_size == 3`
- Tests pass (31/31 — 15 prior + 11 lookahead + 5 new mode-constant tests)

If PASS: iter-v3/060 numbers become the EXPLORATION-mode anchor; cycle 1
EXPLORATIONs at iter-v3/061-068 compare against /060 numbers (NOT /059 numbers).

### Section 8.2 — NULL-RESULT-INFRASTRUCTURE (escalation)

Triggered when ANY of:
- IS Sharpe < +0.50 OR
- OOS Sharpe < 0.0 OR
- BCH IS share < 80%

The 3-seed mode is structurally inadequate for cycle 1 single-axis
discrimination; user must re-evaluate ENSEMBLE_SIZE for EXPLORATION (potentially
raise to 5). The /060 numbers are NOT used as EXPLORATION-mode anchor; cycle 1
sequence pauses pending mode re-design.

### Section 8.3 — FAIL (methodology)

Triggered when:
- Any Critic FAIL on the 13 standard checks (Foundation Audit) OR
- Any Anti-Pattern scan A1-A13 hit

Action: setup-commit revert; QR re-briefs.

### Section 8.4 — Per-Critic Rec #3: BCH IS contribution constraint

The BCH IS share band [80%, 100%] in Section 8.1 PASS criterion is the
operationalization of Critic Rec #3 under EXPLORATION mode. The mandate is
satisfied by including BCH IS share as a PASS gate.

### Section 8.5 — Cycle 1 EXPLORATION cadence

This is iter-v3/060 = cycle 1 EXPLORATION #1 (EXPLORATION-MODE-REFERENCE). Per
`feedback_v3_strict_10_to_1_cadence.md`: 9 more EXPLORATIONs (iter-v3/061-068)
then SEPARATE CONFIRMATION at iter-v3/069. The CONFIRMATION at /069 will run at
CONFIRMATION_ENSEMBLE_SIZE=10 (default, no --exploration flag).

### Section 8.6 — DSR_relative gate informational

Per `feedback_v3_dsr_mode_artifact.md`: EXPLORATION-mode DSR/PSR are informational
only (n_trials=35 3-seed; structurally different from CONFIRMATION-mode
n_trials=1050+). /060 DSR/PSR are not MERGE-gate-relevant at EXPLORATION level.

---

## Section 9 — Library Stack Declaration

UNCHANGED from /059:

- Python 3.13
- lightgbm 4.6.0
- optuna 4.8.0 (n_jobs=1 per `31665f6` revert)
- numpy 2.2.6
- pandas 3.0.0
- scikit-learn 1.8.0
- scipy 1.17.0
- statsmodels 0.14.6
- pyarrow 23.0.1

No new dependencies. Path A makes no library changes.

**Mode-flag refactor at SHA `56f5a30`** extends `_verify_feature_columns(ensemble_size:
int | None)` with mode-aware assertion. Test `test_exploration_mode_uses_3_seeds`
ensures EXPLORATION_ENSEMBLE_SIZE=3 invariant. Test suite size: 31/31 pass
(15 prior + 11 lookahead + 5 new mode-constant tests in
`tests/strategies/ml/test_ensemble_unified.py::TestExplorationConfirmationModeConstants`).

---

## Section 10 — QR Audit Trail

Per `feedback_v3_axis_selection_quant_discipline.md`, this section documents the
QR-driven research path that landed on Path A passive diagnostic.

### Stage 1 — Orchestrator-proposed candidate paths

Cycle 1 EXPLORATION #1 axis = TRX OOS diagnostic per Critic FINAL `0fc18c2`
Recommendation #2 + user-approved cycle 1 sequence. The orchestrator presented
4 sub-paths:
- Path A: Feature importance + label quality diagnostic, NO axis change
- Path B: TRX-specific feature engineering
- Path C: TRX-specific label parameter customization
- Path D: Drop TRX entirely (universe contraction)

The QR was required to make the path choice via EDA-driven quantitative basis
per `feedback_v3_axis_selection_quant_discipline.md`.

### Stage 2 — EDA design (`6ab47b4`)

EDA script `analysis/iteration_v3-060/trx_diagnostic.py` runs 7 questions:
- Q1: Feature importance per symbol — tests Path B candidate evidence
- Q2: TRX label distribution per quarter — tests Path C candidate evidence
- Q3: TRX trade PnL concentration — tests Path D candidate evidence
- Q4: TRX vs BCH vs LDO feature scale divergence — tests Path B candidate evidence
- Q5: TRX trade outcome by ATR regime — tests Path C candidate evidence
- Q6: /058 vs /059 trade roster overlap — quantifies architecture effect
- Q7: RiskV2 vol-scaling effect — tests system-level mechanism

Outputs are 9 committed CSVs + `diagnostic_summary.md`.

### Stage 3 — EDA findings synthesis (Section 2.8 above)

The 7 EDA findings collectively rule out Path B and Path C: TRX feature importance
is normal (Q1), TRX feature scale is within model normalization tolerance (Q4),
TRX label distribution shows regime-skew but no clearly-fixable pattern (Q2),
ATR-regime conditioning does not separate signal from noise (Q5). Path D is
deferred to iter-v3/065+ pending lookback-sensitivity + alt-labeling per
`feedback_insist_on_symbols.md`.

The Q7 finding (RiskV2 vol-scaling anti-Kelly on TRX) is the highest-value
diagnostic discovery: it indicates a SYSTEM-level mechanism that future
iter-v3/061+ should target. iter-v3/060 itself is correctly Path A.

### Stage 4 — Path A EXPLORATION-mode-reference contract (REVISED)

Path A is a no-axis-change diagnostic deliverable. iter-v3/060 backtest invokes
`--exploration` (ENSEMBLE_SIZE=3, ENSEMBLE_SEEDS[0:3]); no other code state change
vs /059 source. The EDA committed at `6ab47b4` is the value-add for cycle 1.
**The original "bit-identical to /059" contract is REPLACED with the
"EXPLORATION-mode-reference establishment" contract** — /060 produces a NEW
3-seed-mode anchor (different numerical baseline than /059's 10-seed
CONFIRMATION-mode anchor) that subsequent cycle 1 EXPLORATIONs (iter-v3/061-068)
compare against. iter-v3/061+ axis selection will be QR-driven again, informed
by /060 EDA findings (Q7 RiskV2 anti-Kelly → vol-scaling recalibration candidate
axis).

### Stage 5 — Setup commit chain

```
Phase A revert SHA:       31665f6 (n_jobs=2 → n_jobs=1 GIL contention)
Phase B-3 unified seed:   ab2d9ac (unified ensemble; outer-seed loop eliminated)
Walk-forward fix SHA:     e149e9d (22-candle embargo at train/test boundary)
RE-ANCHOR #2 BASELINE:    84adfcc (BASELINE_V3.md update)
EDA SHA:                  6ab47b4 (iter-v3/060 TRX diagnostic — Path A evidence)
Setup commit SHA:         2d82079 (original brief + research_brief.md locked)
Backfill SHA:             c19e921 (setup commit SHA backfill into brief)
Mode-flag refactor SHA:   56f5a30 (--exploration → ENSEMBLE_SIZE=3 + tests 31/31)
Brief revision SHA:       (this commit — EXPLORATION-mode contract revision)
Phase 5.5 gate SHA:       (orchestrator-dispatched after this commit)
```

### Stage 6 — Cycle counting

This is iter-v3/060 = cycle 1 EXPLORATION #1 (EXPLORATION-MODE-REFERENCE). RE-ANCHOR
#2 is orthogonal (NOT counted). Cycle 1 EXPLORATIONs run at iter-v3/060-068
(/060 establishes the 3-seed EXPLORATION-mode anchor; /061-068 single-axis
EXPLORATIONs compare against /060); CONFIRMATION at iter-v3/069 (or later per
cadence discipline; do NOT collapse).

### Stage 7 — Brief Section 0.5 wording cleanup (Critic Rec #4)

The prior /059 brief Section 0.5 Stage 3 commit-chain text retained "Optuna
n_jobs=2 (Phase A commit `0a3c30e`)" without acknowledging the `31665f6` revert.
This /060 brief Section 0.5 explicitly states:
"Phase A Optuna n_jobs=2 ATTEMPTED at `0a3c30e`, REVERTED at `31665f6` due to
5x GIL slowdown; current state n_jobs=1."

The inherited "n_jobs=2" wording is corrected at all subsequent Section 9
references.

### Stage 8 — Mode-flag refactor + brief revision (2026-05-13 mid-setup)

**Stage 8**: User directive 2026-05-13 mid-setup — 10 seeds = CONFIRMATION-only.
QE engineering change at SHA `56f5a30` (--exploration flag added; ENSEMBLE_SIZE
mode-aware: 3 for EXPLORATION, 10 for CONFIRMATION). QR brief revision at SHA
(this commit). Path A passive diagnostic upheld; bit-identity contract REPLACED
with EXPLORATION-mode-reference establishment contract. The TRX diagnostic
Q1-Q7 EDA findings (`6ab47b4`) are unchanged — they remain the cycle 1 #1
axis-feeding insights regardless of mode flag.

Tests: 31/31 pass (15 prior + 11 lookahead + 5 new
TestExplorationConfirmationModeConstants in
`tests/strategies/ml/test_ensemble_unified.py`). `ensemble_summary.json` now has
top-level `mode` and `ensemble_size` fields.

---

## Section 11 — Catalog Row Pre-Commit

Pre-committed catalog row template (inserted at `briefs-v3/exploration_catalog.md`
after Phase 8 diary):

```
| iter-v3/060 | <DATE> | Cycle 1 #1 EXPLORATION-MODE-REFERENCE: first 3-seed EXPLORATION-mode run + TRX OOS diagnostic publication (Path A passive; EDA at 6ab47b4; mode flag at 56f5a30) | <IS> | <OOS> | <3-seed EXPLORATION anchor for iter-v3/061-068; RiskV2 Q7 finding informs cycle 1 axis selection> | EXPLORATION-MODE-REFERENCE PASS / NULL-RESULT-INFRASTRUCTURE / FAIL | NO MERGE — Path A passive diagnostic; EDA deliverable; cycle 1 3-seed anchor established |
```

Expected classification: PASS (EXPLORATION-MODE-REFERENCE) per Section 8.1 if /060
numbers fall within predicted bands (IS [+0.85, +1.15], OOS [+0.30, +0.85]) and
BCH IS share in [80%, 100%]. If falsifier fires (IS < +0.50 or OOS < 0.0 or BCH
share < 80%), classification flips to NULL-RESULT-INFRASTRUCTURE indicating
3-seed mode is structurally inadequate for cycle 1 axis-attribution discrimination
— user re-evaluates ENSEMBLE_SIZE for EXPLORATION (potentially raise to 5).

---

**END OF BRIEF — Phase 5 complete (revised under EXPLORATION-mode architecture).**

**Next**: Engineer dispatches Phase 5.5 gate (orchestrator's call), then Phase 6
backtest launch (run_baseline_v3.py with `--exploration` flag; ITERATION_LABEL
v3-060). Wall-clock target: 2h EXPLORATION cap (3-seed n_trials=35).
