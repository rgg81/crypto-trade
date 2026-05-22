# iter-v3/130 Research Brief — Cycle-7 EXPLORATION #9 — Bar-interval axis (4h base candles) WITH closed-loop Optuna-re-training simulator at 4h-density proxy

**Axis**: BAR-INTERVAL transition from 8h base candles to 4h base candles for the BCH/LDO/TRX universe. 2× sample density (~28,274 IS candles vs 14,137 at 8h). K=21 triple-barrier label horizon becomes 84h ≈ 3.5 days at 4h (HALVED from 7 days at 8h). All other architecture inherited from /121: 14-feature V3_FEATURE_COLUMNS_TOP_N, /116 no_confirm primitive, 7-gate RiskV2 (with /127 binary brake disabled + /129 continuous scaling disabled — both axes CLOSED at /129), single-axis bar-interval variation.

**Lineage discipline**: Cycle-7's RISK-PRIMITIVE axis class CLOSED at /129 (binary /127 + continuous /129; 2/2 NEGATIVE-catastrophic; Optuna-trajectory-shift channel TRIPLE-validated across /127 RISK-PRIMITIVE binary + /128 UNIVERSE + /129 RISK-PRIMITIVE continuous). Per `feedback_v3_optuna_trajectory_shift_finding.md` EXTENSION at /128 closeout, ANY axis changing the Optuna training-objective domain requires closed-loop Optuna-re-training simulator as load-bearing pre-flight gate. **Bar-interval IS in the expanded scope** (per /128 EXTENSION explicit enumeration). The /130 EDA operates the simulator at 4h-density proxy via bootstrap upsampling of /121's IS trade roster (the only available data substrate since 4h native data does not yet exist on disk).

**Cycle**: 7 EXPLORATION slot **#9 of 10**. Per `feedback_v3_strict_10_to_1_cadence.md` strict 10:1 cadence: 10 EXPLORATIONs (/122–/131) + 1 CONFIRMATION (/132). Cycle-7 catalog state at /129 closeout: **8/8 NEGATIVE** (7 catastrophic, 1 INERT; 0 PROMISING).

**Anchor (per-criterion annotation)**: PUBLIC = /121 multi-seed CONFIRMATION-MERGE BASELINE (IS monthly Sharpe **+1.3108** / OOS monthly Sharpe **+0.9682**). ADJUSTED = /121 architecturally-adjusted EXPLORATION-mode estimate (IS ≈ +1.06 / OOS ≈ +0.85) per `feedback_v3_dsr_mode_artifact.md` 3-seed-vs-10-seed proba-averaging compression factor.

---

## Section 0 — Data Split declaration

`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` are UNCHANGED. Sacred constants immutable.

- **IS window**: 4h candle stream from per-symbol earliest 4h candle close through `OOS_CUTOFF_DATE = 2025-03-24` (exclusive).
- **OOS window**: `OOS_CUTOFF_DATE = 2025-03-24` through current data extent (2026-05-21).
- **Walk-forward training window**: 24 calendar months ending at each test-month's start; rolling by 1 month. UNCHANGED in calendar terms; the candle-count grows ~2×.
- **Bar interval**: **4h (NEW; primary axis change)**. REVERT-prepared: if backtest catastrophe, /131 can revert to 8h baseline.
- **Universe**: BCH/LDO/TRX (UNCHANGED from /121).

**Hand-chosen parameter declaration (per `feedback_v3_brief_parameter_provenance.md`)**:

| Parameter | Value | Provenance |
|---|---|---|
| V3_MODELS universe | **BCHUSDT + LDOUSDT + TRXUSDT** | INHERITED from /121 (UNCHANGED) |
| V3_FEATURE_COLUMNS_TOP_N | **14 features** (UNCHANGED from /121) | INHERITED from /121 |
| **Bar interval** | **4h (NEW)** | **CHOSEN axis variation** |
| `enable_per_symbol_drawdown_brake` | **False** (axis CLOSED at /127) | INHERITED from /129 REVERT |
| `enable_per_symbol_drawdown_scaling` | **False** (axis CLOSED at /129) | NEW REVERT (was True at /129) |
| `enable_no_confirm_exit` | True | INHERITED from /121 |
| `no_confirm_trigger_atr` | 0.50 | INHERITED from /121 |
| `no_confirm_k_candles` | 4 | INHERITED from /121 |
| Triple-barrier K | 21 | INHERITED from /121 (UNCHANGED in candle count; absolute time CHANGES: 84h = 3.5d at 4h vs 168h = 7d at 8h) |
| ATR multipliers | (2.0, 1.0) | INHERITED from /121 |
| REQUIRED_GAP | 66 = (21+1)×3 | INHERITED from /121 (UNCHANGED in candle count) |
| ENSEMBLE_SIZE | 3 (EXPLORATION mode) | INHERITED EXPLORATION default per `feedback_v3_outer_seed_cap_2_v3.md` |
| n_trials | 35 | INHERITED EXPLORATION default per `feedback_v3_exploration_n_trials_35.md` |

**ZERO new features added in /130.** The structural changes vs /121 are:
1. NEW bar interval = 4h (vs /121's 8h)
2. /127 and /129 axes REVERT (binary brake + continuous scaling both disabled — both axis class CLOSED)
3. Data pipeline change: download 4h klines + regenerate 4h features
4. Runner changes: add "4h" to --bar-interval choices; adjust features_v3 cache paths for 4h; verify REQUIRED_GAP in candle-count terms

**Auditable temporal fence**: the EDA (`analysis/iteration_v3-130/`, commit `ccc0446`) was committed in ONE atomic commit BEFORE this brief. The closed-loop Optuna-re-training simulator strictly enforces:
- IS-only fence at data load: `is_trades` from `reports-v3/iteration_v3-121/in_sample/trades.csv` only (close_time < OOS_CUTOFF_MS).
- T3a 8h baseline + T3b 4h proxy simulators use IS-only bootstrap resamples; no OOS data informs simulator distribution.
- All pre-flight gate decisions (G1, G2, G3) are based on IS-only computations; no OOS metrics referenced in gate logic.

---

## Section 0.5 — Iteration Type Declaration

- **TYPE**: `EXPLORATION` (cycle-7 slot **#9 of 10**; BAR-INTERVAL axis class; 4h base candles)
- **CLI invocation**: `uv run python run_baseline_v3.py --exploration --n-trials 35 --clean-oof --bar-interval 4h`
- **ENSEMBLE_SIZE**: 3 (EXPLORATION default per `feedback_v3_outer_seed_cap_2_v3.md`)
- **n_trials**: 35 (per `feedback_v3_exploration_n_trials_35.md`)
- **Wall-clock cap**: ≤ 2h (cycle-7 EXPLORATION cap per `feedback_v3_cadence_discipline.md`); empirically may exceed at 4h-density (2× candles = ~30% wall-clock overhead) — declared HIGH-RISK on wall-clock at single-seed budget
- **Single axis variation**: bar-interval 8h → 4h. Labels, features, universe, ensemble seeds, Optuna search space, /116 no_confirm primitive, ATR multipliers, K=21 horizon (in candle-count) — ALL bit-identical to /121 in candle-count terms.

**Pre-launch data pipeline**: 4h native kline data does NOT yet exist on disk. Setup commit MUST first download via:
```bash
uv run crypto-trade fetch --symbols BCHUSDT,LDOUSDT,TRXUSDT --intervals 4h
```
And regenerate 4h features:
```bash
uv run crypto-trade features --symbols BCHUSDT,LDOUSDT,TRXUSDT --interval 4h --track v3 --format parquet
```
The setup commit's smoke test asserts both 4h CSVs and 4h feature parquets exist before backtest launch.

---

## Section 1 — Hypothesis

> Switching from 8h to 4h base candles for the BCH/LDO/TRX universe lifts EXPLORATION-mode IS monthly Sharpe by Δ ∈ [−0.30, +0.40] vs the architecturally-adjusted /121 EXPLORATION-mode reference (~+1.06) AND OOS monthly Sharpe by Δ ∈ [−0.30, +0.40] vs /121 OOS +0.9682. The 4h cadence provides 2× sample density at single-seed budget, potentially reducing Optuna trajectory variance and surfacing /121-comparable trajectories despite the structural fragility of the /121 IS-leg lift at single-seed budget (per `feedback_v3_optuna_trajectory_shift_finding.md` /129 closeout EXTENSION lesson). The HALVED label horizon (3.5 days vs 7 days at K=21) shifts the target return regime from medium-cycle to short-cycle; this may improve or degrade signal quality depending on whether 4h-cycle structure is more or less stationary than 8h-cycle structure across the IS window. OR the 4h axis is FALSIFIED at production with the Optuna-trajectory-shift channel signature observed at /127/128/129 (IS Jaccard vs /121 reference at the same-symbol open-time level < 0.70 OR catastrophic IS Sharpe < +0.91), closing the bar-interval axis for cycle-7 and confirming the channel generalization extends to BAR-INTERVAL (the third axis class category in the EXTENSION enumeration).

**Why these prediction bands are WIDE (HIGH-RISK posture)**: The T3b 4h proxy simulator (the load-bearing pre-flight gate per `feedback_v3_optuna_trajectory_shift_finding.md` EXTENSION) DETECTED minimal distribution shift vs T3a 8h baseline at the proxy density:
- T3a 8h baseline: mean **0.395**, std **0.20**, max **0.778**, frac ≥ 0.91 = **0.0%**
- T3b 4h proxy: mean **0.391**, std **0.20**, max **0.804**, frac ≥ 0.91 = **0.0%**
- T3c relative improvement (delta_mean): **-0.0043** (essentially zero)

**Pre-flight gate decision**: **G1 FAIL** at frac ≥ 0.91 = 0.0% (gate threshold 60%). The gate threshold 0.91 derives from /121's multi-seed reference +1.31 - 0.40 catastrophic threshold; at single-seed simulator space, this threshold is **structurally unreachable** because the underlying single-seed baseline is ~0.39, not 1.31. **The meaningful signal is the relative improvement delta_mean = -0.0043, which is essentially zero**: the 4h proxy via bootstrap upsampling does NOT predict materially-different IS Sharpe distribution vs 8h baseline.

The wide prediction bands reflect honest uncertainty:
- IS lower bound −0.30 accommodates the proxy-limitation downside: the bootstrap-upsample proxy under-estimates Optuna's response to actual 4h-density training (different hyperparameter region exploration that the trade-level resample cannot capture)
- IS upper bound +0.40 accommodates the proxy-limitation upside: actual 4h training MAY produce HIGHER Sharpe than the proxy because Optuna can search a deeper hyperparameter region with 2× data density
- OOS bands matched to IS (the bar-interval transition affects both IS and OOS uniformly; no asymmetric mechanism predicted)

**The CASE FOR PROMISING**:
- 4h density may reduce Optuna trajectory variance at single-seed budget (per /129 closeout lesson 3 — the /121 IS lift is fragile to perturbations at single-seed; denser sampling could compensate).
- Bar-interval changes are structurally orthogonal to the Optuna-trajectory-shift channel mechanism (per Critic FINAL Rec 1 at /129: "Bar-interval changes do NOT modify Optuna training-objective weight distribution — they change data discretization"). The channel may not apply.
- T4 feature stability proxy PASS (autocorr std < 0.10 all 3 symbols); T5 ADF PASS (all p < 0.05) — feature transferability is plausible.
- Funding-cycle-half alignment: 4h = 1/2 funding period, so features at candle close are funding-phase-aware.

**The CASE AGAINST PROMISING**:
- T3 simulator G1 FAIL at gate threshold — though the threshold is structurally unreachable at single-seed budget, the relative improvement delta_mean = -0.0043 is unfavorable.
- Cycle-7 base rate: 8/8 NEGATIVE through /129; PROMISING-class prior probability empirically depressed.
- HALVED label horizon (3.5 days vs 7 days) may not match crypto market cycle structure; many alts show 5-7 day mean-reversion cycles that 3.5-day labels would miss.
- 4h native data does NOT exist on disk; setup commit risk: fetch + features regen errors block backtest launch.
- 4h-feature recalibration risk: V3_FEATURE_COLUMNS_TOP_N's rolling-window features (range_realized_vol_50, hurst_100, etc.) cover halved absolute time spans at 4h (50×4h = 200h vs 50×8h = 400h); the same features compute over different historical windows.

---

## Section 2 — EDA backing + closed-loop Optuna-re-training simulator distribution

The EDA at `analysis/iteration_v3-130/` (SHA `ccc0446`) commits 6 result tables BEFORE this brief per `feedback_v3_axis_selection_quant_discipline.md`.

### T1 — Bar-interval candidate catalog

The three candidates evaluated:

| Option | Bar interval | Sample density vs 8h | K=21 label horizon | Data on disk | QR rec |
|---|---:|---:|---:|---|---|
| 1 | **4h** | **2.0×** | 84h = 3.5 days | No | **PRIMARY** |
| 2 | 12h | 0.67× | 252h = 10.5 days | No | TERTIARY |
| 3 | Multi-offset 12h (2 offsets) | 1.33× | 252h = 10.5 days | No | SECONDARY |

QR adjudication: Option 1 (4h) selected per Critic FINAL Rec 1 PRIMARY at /129 closeout + density-lift rationale (2× sample density at single-seed budget may reduce Optuna trajectory variance and surface /121-comparable trajectories).

### T2 — Data depth / sample count proxy vs /121 IS at K=21

| Symbol | 8h IS candles | 4h IS candles (projected) | 12h IS candles (projected) |
|---|---:|---:|---:|
| BCHUSDT | 5,727 | 11,454 | 3,818 |
| LDOUSDT | 2,741 | 5,482 | 1,827 |
| TRXUSDT | 5,669 | 11,338 | 3,779 |
| **PORTFOLIO** | **14,137** | **28,274** | **9,424** |

Trade-rate proxy at 4h: **346 IS trades** projected (vs /121's 173), assuming signal-emission rate per candle is invariant. This exceeds the 130 OOS trade-rate floor by 2.66× at the same proportion.

### T3 — Closed-loop Optuna-re-training simulator (LOAD-BEARING per /128 Critic Rec 2 EXTENSION)

The pre-flight gate per `feedback_v3_optuna_trajectory_shift_finding.md` EXTENSION at /128 closeout.

**Methodology**: For each (outer_seed, training_window_start) configuration (N=10 outer_seeds × 3 training-window-starts = 30 configurations), construct a bootstrap sample of /121 IS trades (resample within trade-month groups to preserve regime structure; outer_seed controls resample randomness; training_window_start shifts regime anchor month). At bar-interval density multiplier > 1.0, simulate additional trades drawn from the bootstrap distribution scaled by (multiplier - 1) — proxy for 4h-density additional signal emissions. Compute IS monthly Sharpe on the resampled trade roster. The DISTRIBUTION of IS Sharpe across the 30 configurations captures the Optuna-trajectory variance at the simulated density.

**T3a — 8h baseline simulator (reference)**:

| Statistic | Value |
|---|---:|
| Mean IS Sharpe | **0.3951** |
| Std | 0.2200 |
| Min | 0.0202 |
| Q25 | 0.2422 |
| Q50 (median) | 0.3370 |
| Q75 | 0.5672 |
| Max | 0.7787 |
| **Frac ≥ 0.91 (gate threshold)** | **0.0% (G1 FAIL)** |
| **Frac < 0.50 (catastrophic)** | **66.7%** |

**T3b — 4h proxy simulator (density multiplier = 2.0×)**:

| Statistic | Value |
|---|---:|
| Mean IS Sharpe | **0.3908** |
| Std | 0.2006 |
| Min | 0.1080 |
| Q25 | 0.2500 |
| Q50 (median) | 0.3248 |
| Q75 | 0.5707 |
| Max | 0.8041 |
| **Frac ≥ 0.91 (gate threshold)** | **0.0% (G1 FAIL)** |
| **Frac < 0.50 (catastrophic)** | **66.7%** |

**T3c — Relative improvement 4h vs 8h**:

| Metric | Value | Interpretation |
|---|---:|---|
| Δ mean (4h − 8h) | **-0.0043** | Essentially zero; 4h proxy does NOT predict materially-different IS Sharpe vs 8h baseline at single-seed simulator space |
| Δ std (4h − 8h) | -0.0170 | Slight variance reduction at 4h (favorable but small) |
| Δ Q75 (4h − 8h) | +0.0035 | Top-quartile preserved at 4h |
| Δ Max (4h − 8h) | +0.0254 | Top simulator outcome slightly higher at 4h |

**Pre-flight gate decision G1**: **FAIL at absolute threshold** (frac ≥ 0.91 = 0.0% vs gate 60%). However, the gate threshold 0.91 derives from /121's multi-seed reference (+1.31) minus 0.40 catastrophic threshold; at single-seed simulator space, the underlying baseline is ~0.39 not 1.31, making the gate **structurally unreachable**. **The meaningful signal is the relative improvement delta_mean = -0.0043**, which is essentially zero — the proxy does NOT predict directional improvement.

**Critical PROXY LIMITATION** disclosure: The simulator bootstrap-upsamples /121's IS trade roster from 8h trade decisions; it cannot capture Optuna's response to actual 4h-density training (different (depth, colsample, reg_lambda) search regions that trade-level resampling cannot reproduce). The production 4h backtest may produce HIGHER or LOWER Sharpe than the proxy predicts. The simulator's primary utility at /130 is detecting the **regime** of production outcome (within first sigma of mean 0.39, std 0.20 = expected range 0.19-0.59 at single-seed); production within this range is expected; production outside this range (either above +1.0 or below 0.0) triggers methodology defects classification.

### T4 — Feature stability proxy at 8h sub-windows

Per-symbol return autocorrelation lag-1 stability across 6-month sub-windows:

| Symbol | n sub-windows | autocorr_lag1 mean | autocorr_lag1 std | Stability proxy PASS |
|---|---:|---:|---:|:---:|
| BCHUSDT | 10 | 0.0132 | 0.0826 | PASS (< 0.10) |
| LDOUSDT | 5 | -0.0074 | 0.0464 | PASS |
| TRXUSDT | 10 | 0.0032 | 0.0535 | PASS |

All 3 symbols pass the stability proxy threshold (autocorr std < 0.10 across sub-windows), suggesting feature transferability from 8h to 4h is plausible.

### T5 — ADF stationarity at 8h sub-windows

| Symbol | n sub-windows | ADF p-value max | ADF stationarity PASS at p<0.05 |
|---|---:|---:|:---:|
| BCHUSDT | 5 | 8.94e-08 | PASS |
| LDOUSDT | 2 | 0.00 | PASS |
| TRXUSDT | 5 | 1.31e-23 | PASS |

All 3 symbols pass ADF stationarity at p < 0.05 across all sub-windows. Log-returns stationary across the IS window.

### T6 — Pre-flight gate decision

| Gate | Pass | Detail |
|---|:---:|---|
| **G1 — Closed-loop Optuna-re-training simulator** (LOAD-BEARING) | **FAIL** | Frac ≥ 0.91 = 0.0% < 60% gate threshold (structurally unreachable at single-seed); meaningful signal Δ mean = -0.0043 (essentially zero) |
| G2 — Feature stability proxy (INFORMATIONAL) | PASS | All 3 symbols autocorr std < 0.10 |
| G3 — ADF stationarity (INFORMATIONAL) | PASS | All 3 symbols ADF p < 0.05 across sub-windows |

**Decision**: **GO_HIGH_RISK** per PRIME DIRECTIVE (`brief + backtest. NO EDA-kill`). G1 FAIL triggers HIGH-RISK posture in Section 7 modal expectation distribution. The brief proceeds to backtest; the falsifiers in Section 4 are calibrated to detect the Optuna-trajectory-shift channel via Jaccard binding adapted for bar-interval changes.

---

## Section 3 — Proposed Changes (single axis)

### 3.1 NEW bar-interval = 4h

The single structural change vs /121 is:

```python
# run_baseline_v3.py argparse extension
parser.add_argument(
    "--bar-interval",
    type=str,
    default="8h",
    choices=["8h", "24h", "4h"],  # NEW: 4h added
    help=(
        "iter-v3/130: 4h bar interval added. Native Binance 4h klines downloaded "
        "via fetcher; 4h features cached at data/features_v3_4h/. "
        "REQUIRED_GAP=66 unchanged (= (21+1)×3 in candle-count terms). "
        "K=21 label horizon at 4h = 84h = 3.5 days (HALVED from 168h = 7 days at 8h). "
        "ENSEMBLE_SIZE/n_trials/Optuna search unchanged from 8h."
    ),
)
```

### 3.2 features_v3 cache directory + 4h ingestion

```python
# run_baseline_v3.py: bar-interval-conditional features directory
if args.bar_interval == "4h":
    features_dir = data_dir / "features_v3_4h"
elif args.bar_interval == "24h":
    features_dir = data_dir / "features_v3_24h"
else:  # 8h default
    features_dir = data_dir / "features_v3"
```

### 3.3 BacktestConfig + walk-forward gap

REQUIRED_GAP stays 66 in candle-count terms (= (21+1)×3 = 66 for K=21 with 3 symbols at any bar interval). The walk-forward training-month window stays 24 calendar months; the number of candles per WF training window doubles at 4h vs 8h.

```python
# _verify_label_leakage_gap()
if bar_interval == "4h":
    # Same gap in candle count; absolute time is halved
    # 66 candles × 4h = 264h ≈ 11 days gap (vs 22 days at 8h)
    expected_gap = 66
elif bar_interval == "24h":
    expected_gap = 72
else:  # 8h
    expected_gap = 66
```

### 3.4 Revert /127 + /129 axes

- `enable_per_symbol_drawdown_brake = False` (axis CLOSED at /127; preserved REVERT)
- `enable_per_symbol_drawdown_scaling = False` (axis CLOSED at /129; NEW REVERT vs /129)

### 3.5 ITERATION_LABEL = "v3-130"

Standard iteration label override in `run_baseline_v3.py`.

### 3.6 `_canonical_v059` accretion guard update

The `_canonical_v059` accretion guard in `run_baseline_v3.py` adds entry: `bar_interval="4h"` to the expected post-/121 config (only when `--bar-interval 4h` is passed; defaults remain at 8h for backward compatibility).

**ZERO changes to**: V3_MODELS (stays BCH/LDO/TRX), V3_FEATURE_COLUMNS_TOP_N (stays 14), DEFAULT_ATR_MULTIPLIERS (stays (2.0,1.0)), label_mode (stays triple_barrier), enable_no_confirm_exit (stays True), no_confirm_trigger_atr (stays 0.50), no_confirm_k_candles (stays 4), 7-gate RiskV2 stack (gates 1-6 unchanged), REQUIRED_GAP in candle count (stays 66), Optuna search space (unchanged). `enable_per_symbol_drawdown_brake` stays False (REVERT preserved from /129). `enable_per_symbol_drawdown_scaling` REVERTS to False (NEW vs /129).

---

## Section 4 — Pre-registered Falsifiers (binding)

Each falsifier is pre-registered at brief commit time. Engineer must report the falsifier outcomes in Section 8 of the engineering report. Critic adjudicates Section 8 truthiness against artifact data.

### F1 — IS monthly Sharpe band

**Hypothesis**: IS monthly Sharpe ∈ [−0.30, +0.40] vs the architecturally-adjusted /121 EXPLORATION-mode reference (~+1.06).
- BAND: observed IS Sharpe − 1.06 ∈ [−0.30, +0.40] → IS observed ∈ [0.76, 1.46].
- FALSIFIER FIRES IF: observed IS Sharpe < 0.76 OR observed IS Sharpe > 1.46.

### F2 — OOS monthly Sharpe band

**Hypothesis**: OOS monthly Sharpe ∈ [−0.30, +0.40] vs /121 OOS +0.9682.
- BAND: observed OOS Sharpe − 0.9682 ∈ [−0.30, +0.40] → OOS observed ∈ [0.67, 1.37].
- FALSIFIER FIRES IF: observed OOS Sharpe < 0.67 OR observed OOS Sharpe > 1.37.

### F3 — IS-vs-OOS dissociation

**Hypothesis**: |IS Δ − OOS Δ| < 0.50.
- FALSIFIER FIRES IF: |IS observed − 1.06 − (OOS observed − 0.9682)| > 0.50.
- Triggers SUSPICIOUS-OOS-DOMINANT classification.

### F4 — Trade-rate floor (informational, NOT binding for EXPLORATION)

Trade-rate floor of ≥130 OOS trades, ≥10 trades/month OOS, ≥50 IS trades/symbol is INFORMATIONAL for EXPLORATION class per `feedback_v3_trade_rate_floor_bundle_level.md`. /121 baseline had 173 IS / 98 OOS at 8h. At 4h with 2× density, the trade-rate proxy projects 346 IS / 196 OOS — well above floors. F4 PASS expected; informational fail still possible if 4h signal-emission rate is lower than 8h-proxy projection.

### F5 — Per-symbol cascade failure

If 2 of 3 symbols (BCH, LDO, TRX) produce IS contribution < 0 PnL OR 2 of 3 symbols OOS contribution < 0 PnL, classify as PROMISING-cohort-fragile (subtype of NEGATIVE-class).

### F6 — **Optuna-trajectory-shift binding falsifier (per /128 Critic Rec 2 EXTENSION; ADAPTED for bar-interval)**

**Hypothesis (the LOAD-BEARING falsifier)**: production IS trade-roster Jaccard vs /121 anchor ≥ 0.70 (adapted for bar-interval at same-symbol open-time match-resolution).
- FALSIFIER FIRES IF: IS Jaccard vs /121 < 0.70.
- **ADAPTATION for bar-interval**: at 4h, open_time values are at 4h boundaries (0, 4h, 8h, 12h, 16h, 20h UTC); /121's open_times are at 8h boundaries (0, 8h, 16h UTC). The 4h roster will include trades at open_times that do NOT correspond to 8h boundaries (e.g., 4h, 12h, 20h UTC) which structurally cannot match /121 — these are NEW trades by virtue of the bar-interval change, not Optuna re-convergence. Jaccard computation:
  - For trades at 8h-boundary open_times (0, 8, 16 UTC): exact open_time match required
  - For trades at 4h-but-not-8h-boundary open_times (4, 12, 20 UTC): cannot match by definition; counted as 4h-axis-introduced trades
  - Reported Jaccard: |{4h trades at 8h boundaries} ∩ /121 IS trades| / |{4h trades at 8h boundaries} ∪ /121 IS trades|
- Triggers automatic NEGATIVE-Optuna-trajectory-shift classification per `feedback_v3_optuna_trajectory_shift_finding.md`. The lift cannot be attributed to the bar-interval mechanism if Optuna re-converged to a different region at the 8h-aligned trade-emission boundary.

### F7 — Behavioral-effect predictor binding

**Hypothesis**: IS trade-count change vs /121 anchor in [+50%, +150%] (4h's 2× density should produce 2× trade count proportionally; broad band to accommodate signal-emission rate variance).
- /121 baseline: 173 IS trades; expected /130: [260, 433] IS trades.
- FALSIFIER FIRES IF: IS trade count < 260 OR > 433.
- Triggers methodology-defect classification: 4h either produces signal-emission rate DRAMATICALLY higher than expected (>2.5×, suggesting noise-trading) or DRAMATICALLY lower (<1.5×, suggesting feature/signal degradation at 4h).

### F8 — Top-symbol concentration cap (informational)

If 1 symbol produces > 40% of OOS PnL, classify as concentration-fragile (per `feedback_v3_concentration_is_signal.md`).

### F9 — **NEW: Wall-clock cap binding (cycle-7 procedural)**

**Hypothesis**: backtest wall-clock < 2.5h (1.25× the standard 2h EXPLORATION cap; 4h-density 2× candles adds ~30% wall-clock overhead).
- FALSIFIER FIRES IF: backtest wall-clock > 2.5h.
- Triggers methodology-cap-breach classification: 4h-density is empirically too expensive at single-seed EXPLORATION budget.

---

## Section 5 — Implementation Plan (Phase 6 Engineer scope)

### 5.1 Setup commit

Edit `run_baseline_v3.py`:
1. `ITERATION_LABEL` → `"v3-130"`.
2. `_canonical_v059` accretion guard: add `bar_interval="4h"` expected when `--bar-interval 4h` passed.
3. V3_MODELS UNCHANGED (BCH/LDO/TRX).
4. REQUIRED_GAP=66 UNCHANGED in candle-count terms.
5. `enable_per_symbol_drawdown_brake=False` (preserved REVERT from /129).
6. `enable_per_symbol_drawdown_scaling=False` (NEW REVERT from /129).
7. Add "4h" to --bar-interval choices.
8. Features_v3 cache dir: bar-interval-conditional path.
9. Feature regeneration for 4h: feature parquets must be generated before backtest.

Edit `src/crypto_trade/features_v3/__init__.py` (if needed):
1. Add 4h-aware feature column registration (most features are bar-interval-invariant; rolling-window features may need adjustment if they assume 8h)
2. Verify features that depend on 8h-specific behavior (e.g., funding-cycle alignment) compute correctly at 4h or are skipped

Edit `src/crypto_trade/cli.py` (or features generation CLI):
1. Verify `crypto-trade features --interval 4h --track v3` works
2. Verify output directory is `data/features_v3_4h/`

### 5.2 Pre-launch data pipeline

```bash
# Download 4h klines (Binance native)
uv run crypto-trade fetch --symbols BCHUSDT,LDOUSDT,TRXUSDT --intervals 4h

# Generate 4h features
uv run crypto-trade features --symbols BCHUSDT,LDOUSDT,TRXUSDT --interval 4h --track v3 --format parquet --workers 4
```

### 5.3 Test suite

- Update `tests/test_run_baseline_v3.py` to include a 4h smoke-test variant
- Verify _verify_feature_columns / _verify_label_leakage_gap at 4h
- Verify candle integrity (close_time freshness; forming-candle filter; all features cover full IS window)

### 5.4 Backtest

```bash
uv run python run_baseline_v3.py --exploration --n-trials 35 --clean-oof --bar-interval 4h
```

Wall-clock budget: ≤ 2.5h (HIGH-RISK on wall-clock; 4h-density 2× candles adds ~30% overhead vs 8h's empirical 0.7-1.1h). F9 falsifier fires at >2.5h.

### 5.5 Engineering report

Per `feedback_v3_axis_selection_quant_discipline.md` standard format. Report:
- Per-symbol IS/OOS PnL contribution + WR + trade count
- **F6 LOAD-BEARING (adapted for bar-interval)**: IS trade-roster Jaccard vs /121 anchor at the 8h-aligned-open-time level
- **F7 LOAD-BEARING**: |Δ IS trades vs /121 anchor| in trade-count terms (expected ~2× = ~346)
- Section 8 PER-CRITERION ANCHOR ANNOTATION: F1-F9 outcomes vs prediction bands
- Concentration analysis: top-symbol OOS PnL share
- **Wall-clock report (F9 binding)**

### 5.6 Smoke test (per `feedback_v3_instrumentation_run_log_missing.md` /128/129 closeout)

Setup commit MUST include end-to-end smoke test that verifies:

1. `--bar-interval 4h` parses correctly via argparse
2. 4h CSVs exist at `data/BCHUSDT/4h.csv`, `data/LDOUSDT/4h.csv`, `data/TRXUSDT/4h.csv`
3. 4h feature parquets exist at `data/features_v3_4h/BCHUSDT_4h_features.parquet`, etc.
4. `enable_per_symbol_drawdown_brake=False` AND `enable_per_symbol_drawdown_scaling=False`
5. V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT)
6. V3_FEATURE_COLUMNS_TOP_N has exactly 14 features
7. `_canonical_v059` accretion guard reflects /130 config additions
8. **`run.log` MUST persist** to `reports-v3/iteration_v3-130/run.log` at run end (5-occurrence instrumentation gap fix per /129 closeout)
9. **Per-symbol per-WF-month classifier AUC MUST persist** to `reports-v3/iteration_v3-130/in_sample/per_symbol_walk_forward_auc.csv` AND `reports-v3/iteration_v3-130/out_of_sample/per_symbol_walk_forward_auc.csv` (instrumentation gap fix per /128 closeout)
10. The runner pre-flight prints "Universe: BCH/LDO/TRX | Bar interval: 4h | K=21 (label horizon 84h ≈ 3.5d)"

If any smoke test fails, abort the backtest at setup commit + push fix commits BEFORE the backtest launches.

---

## Section 6 — Risk Mitigation + HIGH-RISK posture declaration

**This iteration runs under HIGH-RISK posture** per the closed-loop Optuna-re-training simulator T3 G1 pre-flight gate FAIL (frac ≥ 0.91 = 0.0% < 60% threshold; absolute threshold structurally unreachable at single-seed budget; relative improvement delta_mean = -0.0043 essentially zero). The HIGH-RISK declaration is structural; it does NOT block the PRIME DIRECTIVE (brief + backtest mandatory).

**Risk mitigations**:

1. **Bar-interval-axis closure-discipline**: this is the FIRST bar-interval attempt in v3 history (excluding /117's 24h multi-offset experiment which closed-narrow). If /130 NEGATIVE, the 4h sub-axis closes; cycle-7 axis menu narrows to /131 = bar-interval variants OR cycle-7-close-early.

2. **F6 Optuna-trajectory-shift Jaccard binding (adapted)**: production IS Jaccard vs /121 (at 8h-aligned open-time level) < 0.70 triggers automatic NEGATIVE classification regardless of headline Sharpe. The bar-interval-axis adaptation handles structural open-time mismatch at 4h boundaries.

3. **F7 behavioral-effect predictor binding (wider band)**: |Δ IS trades vs /121| outside [+50%, +150%] triggers methodology-defect classification. The expected 2× trade-count scaling at 4h-density is honest; wider band accommodates signal-emission rate variance.

4. **F9 wall-clock cap binding (NEW)**: backtest > 2.5h triggers methodology-cap-breach classification. 4h-density should not push EXPLORATION wall-clock beyond ~30% of 8h baseline.

5. **No structural risk mitigations beyond /121 baseline**: 7-gate RiskV2 stack unchanged; /116 no_confirm STAYS ENABLED; /127 binary brake and /129 continuous scaling both REVERTED (both axes CLOSED).

**Why proceed under HIGH-RISK**: per `feedback_v3_qr_axis_creativity_mandate.md` PRIME DIRECTIVE: "brief + backtest. NO EDA-kill." The HIGH-RISK posture is honestly disclosed in Section 7 modal distribution (NEGATIVE-class weight 65%). The closed-loop Optuna-re-training simulator at T3 detected near-zero distribution shift at 4h-density proxy vs 8h baseline; the simulator's primary utility at /130 is detecting **regime** of production outcome (within first sigma of mean 0.39, std 0.20 = expected single-seed range 0.19-0.59). Production within this range is expected; production outside this range (above +1.0 or below 0.0) triggers methodology defects classification.

---

## Section 7 — Pre-registered Modal Expectation Distribution

The modal expectation distribution gives substantial weight to NEGATIVE-class outcomes due to the HIGH-RISK posture from the T3 closed-loop Optuna-re-training simulator G1 FAIL and the cycle-7 base rate (8/8 NEGATIVE through /129). The prior is anchored on:
- Cycle-7 base rate: 8/8 NEGATIVE through /129.
- T3 simulator: mean 0.39 (8h baseline 0.40); 0/30 above 0.91 threshold (structurally unreachable at single-seed); 67% below 0.50 catastrophic; relative improvement essentially zero.
- BUT: /130 is the FIRST bar-interval transition in v3 history; the structural hypothesis (bar-interval is structurally orthogonal to Optuna-trajectory-shift channel) is genuinely novel within v3.
- T4+T5 PASS informational (feature transferability + ADF stationarity plausible).

| Mode | Outcome class | Prior probability | Triggering F1/F2/F6 combo |
|---|---|---:|---|
| 1 | NEGATIVE-catastrophic (IS < 0.76 OR OOS < 0.67) | **30%** | F1 lower OR F2 lower |
| 2 | NEGATIVE-Optuna-trajectory-shift (F6 fires: IS Jaccard < 0.70) | **20%** | F6 |
| 3 | NEGATIVE-INERT (IS ∈ [0.76, 1.06], OOS ∈ [0.67, 0.95]; bands lower-half) | 15% | F1 mid-low + F2 mid-low |
| 4 | NEGATIVE-methodology-defect (F7 or F9 fires) | 5% | F7 or F9 |
| 5 | NEUTRAL (IS ∈ [0.96, 1.16], OOS ∈ [0.77, 1.07]; bands midpoint) | 15% | F1 mid + F2 mid |
| 6 | PROMISING (IS ≥ 1.06 AND OOS ≥ 0.97; both legs at or above /121 ADJUSTED) | 10% | F1 upper + F2 upper |
| 7 | SUSPICIOUS-OOS-DOMINANT (F3 fires: |IS Δ − OOS Δ| > 0.50) | 5% | F3 |

**Total NEGATIVE-class prior**: 70% (Modes 1+2+3+4). **Total PROMISING-class prior**: 10% (Mode 6). **Total NEUTRAL-class prior**: 15% (Mode 5). **Total SUSPICIOUS prior**: 5% (Mode 7).

---

## Section 8 — Falsifier decision tree (first-match-wins, pre-registered)

Apply criteria in order; **first match wins**.

### Criterion 1 — NEGATIVE-catastrophic
**Anchor: PUBLIC** (/121 multi-seed; IS +1.3108 / OOS +0.9682).
**Condition**: IS monthly Sharpe < +0.91 OR OOS monthly Sharpe < +0.67.
**Outcome**: NO-MERGE. EXPLORATION-NEGATIVE-catastrophic.

### Criterion 2 — NEGATIVE-Optuna-trajectory-shift (load-bearing for bar-interval axis)
**Anchor: PUBLIC**.
**Condition**: F6 fires (IS trade-roster Jaccard vs /121 at 8h-aligned open-time level < 0.70) regardless of headline Sharpe.
**Outcome**: NO-MERGE. EXPLORATION-NEGATIVE-Optuna-trajectory-shift. The bar-interval axis closes by methodology channel; the channel generalization extends to BAR-INTERVAL (the third axis class category in the EXTENSION enumeration). Future bar-interval axes (12h, multi-offset 12h, etc.) require closed-loop Optuna-re-training simulators per `feedback_v3_optuna_trajectory_shift_finding.md`.

### Criterion 3 — NEGATIVE-methodology-cap-breach (NEW, NEW per /130 F9)
**Anchor: PROCEDURAL**.
**Condition**: F9 fires (backtest wall-clock > 2.5h).
**Outcome**: NO-MERGE. EXPLORATION-NEGATIVE-methodology-cap-breach. The 4h-density is too expensive at single-seed EXPLORATION budget; future bar-interval axes need wall-clock budget reformulation.

### Criterion 4 — NEGATIVE-behavioral-defect (NEW per /127 carry-forward; ADAPTED for bar-interval)
**Anchor: PUBLIC**.
**Condition**: F7 fires (IS trade-count outside [+50%, +150%] of /121 baseline; expected ~2× at 4h density).
**Outcome**: NO-MERGE. EXPLORATION-NEGATIVE-behavioral-defect. The behavioral-effect predictor misses; 4h signal-emission rate is dramatically inconsistent with the density-proportional projection.

### Criterion 5 — NEGATIVE-INERT
**Anchor: PUBLIC** for IS leg; **ADJUSTED** for OOS leg.
**Condition**: IS monthly Sharpe ∈ [0.91, 1.06] AND OOS monthly Sharpe ∈ [0.67, 0.95]. (Both legs within band but in the lower half.)
**Outcome**: NO-MERGE. EXPLORATION-NEGATIVE-INERT.

### Criterion 6 — NEGATIVE-no-effect
**Anchor: ADJUSTED** (3-seed compression: IS ≈ +1.06 / OOS ≈ +0.85).
**Condition**: IS monthly Sharpe delta in [−0.05, +0.05] vs ADJUSTED AND OOS monthly Sharpe delta in [−0.05, +0.05] vs ADJUSTED.
**Outcome**: NO-MERGE. EXPLORATION-NEGATIVE-no-effect.

### Criterion 7 — SUSPICIOUS-OOS-DOMINANT
**Anchor: ADJUSTED**.
**Condition**: F3 fires (|IS Δ − OOS Δ| > 0.50). Typically: OOS adj-delta > +0.30 AND IS adj-delta < −0.10.
**Outcome**: NO-MERGE. SUSPICIOUS-OOS-DOMINANT per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`.

### Criterion 8 — PROMISING-cohort-fragile
**Anchor: PUBLIC**; F5 evaluated independently.
**Condition**: IS monthly Sharpe ∈ [0.91, 1.46] AND OOS monthly Sharpe ∈ [0.67, 1.37] AND F5 fires (≥2 of 3 symbols negative IS contribution OR ≥2 of 3 symbols negative OOS contribution).
**Outcome**: NO-MERGE. PROMISING-cohort-fragile.

### Criterion 9 — PROMISING-MECHANICAL
**Anchor: PUBLIC**.
**Condition**: IS monthly Sharpe ≥ +1.06 AND OOS monthly Sharpe ≥ +0.97 AND F6 PASS (IS Jaccard vs /121 at 8h-aligned open-time level ≥ 0.70 → 4h-bar-interval can be attributed mechanistically). All 3 symbols positive IS+OOS contribution (analogous to /116 broad-base diagnostic).
**Outcome**: CANDIDATE for bundle assembly at CONFIRMATION. Defer to /132.

### Criterion 10 — PROMISING-strong
**Anchor: PUBLIC** (/121 multi-seed).
**Condition**: IS monthly Sharpe ≥ +1.16 AND OOS monthly Sharpe ≥ +1.07. (Both legs clear /121 PUBLIC + 0.10 buffer.) F6 PASS, F3 PASS.
**Outcome**: CANDIDATE for bundle assembly at CONFIRMATION. Defer to /132.

---

## Section 9 — Acceptance smoke test

The Engineer's setup commit must include an end-to-end smoke test that verifies:

1. `--bar-interval 4h` accepted by argparse in `run_baseline_v3.py`.
2. 4h kline CSVs exist at `data/BCHUSDT/4h.csv`, `data/LDOUSDT/4h.csv`, `data/TRXUSDT/4h.csv`. If MISSING, abort and run `uv run crypto-trade fetch --symbols BCHUSDT,LDOUSDT,TRXUSDT --intervals 4h` first.
3. 4h feature parquets exist at `data/features_v3_4h/BCHUSDT_4h_features.parquet`, `data/features_v3_4h/LDOUSDT_4h_features.parquet`, `data/features_v3_4h/TRXUSDT_4h_features.parquet`. If MISSING, abort and run `uv run crypto-trade features --symbols BCHUSDT,LDOUSDT,TRXUSDT --interval 4h --track v3 --format parquet` first.
4. `enable_per_symbol_drawdown_brake=False` (REVERT preserved from /129).
5. `enable_per_symbol_drawdown_scaling=False` (NEW REVERT from /129).
6. V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT).
7. V3_FEATURE_COLUMNS_TOP_N has exactly 14 features.
8. `_canonical_v059` accretion guard reflects /130 config additions (bar_interval="4h").
9. REQUIRED_GAP=66 verified at 4h bar interval (candle-count terms).
10. **`run.log` persists** to `reports-v3/iteration_v3-130/run.log` at run end (instrumentation gap fix per `feedback_v3_instrumentation_run_log_missing.md`; 5-occurrence pattern).
11. **Per-symbol per-WF-month classifier AUC persists** to `reports-v3/iteration_v3-130/in_sample/per_symbol_walk_forward_auc.csv` AND `reports-v3/iteration_v3-130/out_of_sample/per_symbol_walk_forward_auc.csv` (instrumentation gap fix per /128 closeout).
12. The runner pre-flight prints "Universe: BCH/LDO/TRX | Bar interval: 4h | K=21 (label horizon 84h ≈ 3.5d)".

If any smoke test fails, abort the backtest at setup commit + push fix commits BEFORE the backtest launches.

---

## Section 10 — QR Audit Trail

**EDA commit**: `ccc0446` (analysis/iteration_v3-130/, 6 EDA tables + chosen_config.json + closed-loop Optuna-re-training simulator at 4h-density proxy)

**Brief commit**: this file (to be committed next)

**QR rationale chain**:
1. /129 closeout (Critic FINAL `fd29feb`) recommended PRIMARY = bar-interval axis (multi-offset 12h or 4h base candles): "Sole remaining untested viable axis class for cycle-7. Bar-interval changes do NOT modify Optuna training-objective weight distribution — they change data discretization. Structural orthogonality."
2. The /127 + /128 + /129 finding (`feedback_v3_optuna_trajectory_shift_finding.md` TRIPLE-validated EXTENSION) established that ANY axis changing Optuna training-objective domain requires closed-loop Optuna-re-training simulators as load-bearing pre-flight gate. **Bar-interval is in the EXPANDED SCOPE** per /128 EXTENSION's explicit enumeration.
3. EDA committed BEFORE brief per `feedback_v3_axis_selection_quant_discipline.md`. EDA implements the closed-loop Optuna-re-training simulator at 4h-density proxy via bootstrap upsampling within month-groups (preserves regime structure).
4. T3a 8h baseline simulator: mean 0.395, std 0.22, max 0.778; T3b 4h proxy simulator: mean 0.391, std 0.20, max 0.804; T3c relative improvement delta_mean = -0.0043 (essentially zero).
5. Pre-flight gate G1: FAIL at absolute threshold (0/30 above 0.91; threshold structurally unreachable at single-seed simulator space).
6. Decision: GO_HIGH_RISK per PRIME DIRECTIVE (brief + backtest; NO EDA-kill).
7. Section 7 modal expectation distribution honestly weights NEGATIVE-class at 70% prior (30% catastrophic + 20% Optuna-trajectory-shift + 15% INERT + 5% methodology-defect); PROMISING-class at 10%.

**Critic FINAL adjudication considerations**:
- The HIGH-RISK posture is structurally honest — the simulator distribution at 4h proxy is pre-registered in Section 6 + 7 BEFORE the backtest runs.
- The single axis (bar-interval 8h → 4h) is bit-identical-vs-anchor on 13 of the 14 architecture knobs; only bar_interval changes (and the /127 + /129 axes both REVERT to False which preserves the /121-baseline-equivalent risk stack).
- Wall-clock budget ≤ 2.5h is HIGH-RISK; 4h-density 2× candles adds ~30% overhead vs 8h baseline.
- The T3 closed-loop Optuna-re-training simulator at 4h proxy operationalizes the methodology established at /128 closeout (TRIPLE-validated at /129) for the bar-interval axis class. The proxy limitation (bootstrap upsampling of /121's 8h trade roster cannot capture 4h-density Optuna search-region exploration) is explicitly disclosed.
- F6 Optuna-trajectory-shift Jaccard binding falsifier (Criterion 2) is the LOAD-BEARING binding falsifier per /128 closeout EXTENSION; adapted for bar-interval to handle structural open-time mismatch at 4h boundaries.
- F9 wall-clock cap binding falsifier (NEW at /130) detects methodology-cap-breach if 4h-density exceeds 2.5h at single-seed EXPLORATION budget.
- Section 8 first-match-wins decision tree pre-registered at brief commit time; no post-hoc reclassification allowed.

The /130 axis tests the structural hypothesis that bar-interval changes are orthogonal to the Optuna-trajectory-shift channel. The simulator's near-zero relative improvement (delta_mean = -0.0043) is the honest pre-flight prediction; production observations will validate or falsify the structural hypothesis.

**Closed-loop Optuna-re-training simulator distribution summary**: **N=10 outer-seeds × 3 training-window-starts = 30 configurations**. **T3a 8h baseline**: mean 0.395, std 0.22, 0/30 ≥ +0.91 (gate threshold structurally unreachable at single-seed); 20/30 (66.7%) below 0.50 catastrophic. **T3b 4h proxy**: mean 0.391, std 0.20, 0/30 ≥ +0.91; 20/30 (66.7%) below 0.50. **T3c relative improvement**: delta_mean = -0.0043 (essentially zero). G1 FAIL at absolute threshold; HIGH-RISK posture honestly disclosed in Section 7 modal distribution.

**The simulator's primary value for /130**: detect the regime of production outcome. Expected single-seed range [0.19, 0.59] from simulator mean ± 1σ. Production outside this range triggers:
- Production > +1.0: PROMISING-class (Mode 6); 4h density unlocks /121-comparable trajectory at single-seed budget.
- Production < 0.0: NEGATIVE-catastrophic; 4h density introduces unfavorable Optuna trajectory.
- Production in [0.0, 0.5]: NEGATIVE-INERT or NEGATIVE-no-effect; 4h does not provide directional improvement.
- Production in [0.5, 1.0]: NEUTRAL or PROMISING-MECHANICAL pending F6 Jaccard binding.
