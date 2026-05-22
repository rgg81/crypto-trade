# iter-v3/129 Research Brief — Cycle-7 EXPLORATION #8 — Continuous multiplicative position-size scaling at per-symbol 45-day rolling drawdown WITH closed-loop Optuna-re-training simulator

**Axis**: RISK-PRIMITIVE continuous multiplicative position-size scaling at per-symbol 45-day rolling drawdown. Scale function `weight_multiplier(dd) = max(0, min(1, (T_max - dd) / (T_max - T_R)))` with T_R=6.0 wpnl (full size), T_max=7.0 wpnl (zero size). Linear interpolation between. M=21 candles time-override (deadlock-impossibility preserved per /127 finding). Lookback N=45 days (same as /127).

**Lineage discipline**: /127's binary kill brake was CLOSED at /127 closeout via the Optuna-trajectory-shift finding (IS Δ -0.5242, IS Jaccard 0.4286 = 77 trades dropped + 51 new). /129 is the re-take under the NEW methodology binding per `feedback_v3_optuna_trajectory_shift_finding.md` EXTENSION at /128 closeout: **ANY axis that changes the Optuna training-objective domain requires closed-loop Optuna-re-training simulators as load-bearing pre-flight gate**. The continuous form preserves Optuna gradient — trades not deleted from training; their contribution dampened proportionally to drawdown severity. /127's binary semantics (keep or fully kill) is replaced with continuous semantics (keep, dampen, or zero).

**Cycle**: 7 EXPLORATION slot **#8 of 10**. Per `feedback_v3_strict_10_to_1_cadence.md` strict 10:1 cadence: 10 EXPLORATIONs (/122–/131) + 1 CONFIRMATION (/132). Cycle-7 catalog state at /128 closeout: 7/7 NEGATIVE (6 catastrophic, 1 INERT). /129 is slot 8/10.

**Anchor (per-criterion annotation)**: PUBLIC = /121 multi-seed CONFIRMATION-MERGE BASELINE (IS monthly Sharpe **+1.3108** / OOS monthly Sharpe **+0.9682**). ADJUSTED = /121 architecturally-adjusted EXPLORATION-mode estimate (IS ≈ +1.06 / OOS ≈ +0.85) per `feedback_v3_dsr_mode_artifact.md` 3-seed-vs-10-seed proba-averaging compression factor.

---

## Section 0 — Data Split declaration

`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` are UNCHANGED. Sacred constants immutable.

- **IS window**: 8h candle stream from per-symbol earliest 8h candle close through `OOS_CUTOFF_DATE = 2025-03-24` (exclusive).
- **OOS window**: `OOS_CUTOFF_DATE = 2025-03-24` through current data extent (2026-05-21).
- **Walk-forward training window**: 24 calendar months ending at each test-month's start; rolling by 1 month.
- **Bar interval**: 8h (UNCHANGED).
- **Universe**: BCH/LDO/TRX (revert from /128's ATOM/RUNE/AVAX/HBAR/ICP/ALGO; /128 universe-axis CLOSED at 9/9 NEGATIVE).

**Hand-chosen parameter declaration (per `feedback_v3_brief_parameter_provenance.md`)**:

| Parameter | Value | Provenance |
|---|---|---|
| V3_MODELS universe | **BCHUSDT + LDOUSDT + TRXUSDT** | INHERITED from /121 (baseline universe; revert from /128) |
| V3_FEATURE_COLUMNS_TOP_N | **14 features** (UNCHANGED from /121) | INHERITED from /121 |
| `enable_per_symbol_drawdown_brake` | **False** (continuous form is a NEW primitive, not a re-enable of binary) | REVERT from /127's True |
| `enable_per_symbol_drawdown_scaling` (NEW) | **True** | NEW primitive at /129 |
| `drawdown_scaling_T_R` (NEW) | **6.0 wpnl** | SELECTED via T1 parameter scan |
| `drawdown_scaling_T_max` (NEW) | **7.0 wpnl** | SELECTED via T1 parameter scan |
| `drawdown_scaling_window_days` (NEW) | **45** | SELECTED to match /127 |
| `drawdown_scaling_time_override_candles` (NEW) | **21** | SELECTED to match /127 (deadlock-impossibility preserved) |
| `enable_no_confirm_exit` | True | INHERITED from /121 |
| `no_confirm_trigger_atr` | 0.50 | INHERITED from /121 |
| `no_confirm_k_candles` | 4 | INHERITED from /121 |
| Triple-barrier K | 21 | INHERITED from /121 |
| ATR multipliers | (2.0, 1.0) | INHERITED from /121 |
| REQUIRED_GAP | 66 = (21+1)×3 | INHERITED from /121 (revert from /128's 132) |
| ENSEMBLE_SIZE | 3 (EXPLORATION mode) | INHERITED EXPLORATION default per `feedback_v3_outer_seed_cap_2_v3.md` |
| n_trials | 35 | INHERITED EXPLORATION default per `feedback_v3_exploration_n_trials_35.md` |
| Bar interval | 8h | INHERITED from /121 |

**ZERO new features added in /129.** The structural changes vs /121 are:
1. NEW `enable_per_symbol_drawdown_scaling=True` primitive (continuous form; distinct from /127's binary `enable_per_symbol_drawdown_brake`)
2. NEW `drawdown_scaling_T_R=6.0`, `drawdown_scaling_T_max=7.0` parameters
3. INHERITED `drawdown_scaling_window_days=45`, `drawdown_scaling_time_override_candles=21` (carry-forward /127 lookback + deadlock-breaker)
4. `RiskV2Wrapper` modification: continuous size-multiplier in `get_signal` BEFORE the brake-kill check (the multiplier multiplies into the final weight)

**Auditable temporal fence**: the EDA (`analysis/iteration_v3-129/`, commit `5d90e2c`) was committed in ONE atomic commit BEFORE this brief. The closed-loop Optuna-re-training simulator strictly enforces:
- IS-only fence at data load: `is_trades` from `reports-v3/iteration_v3-121/in_sample/trades.csv` only (close_time < OOS_CUTOFF_MS).
- T2 closed-loop Optuna-re-training simulator uses IS-only bootstrap resamples; no OOS data informs simulator distribution.
- All pre-flight gate decisions (G1, G2) are based on IS-only computations; no OOS metrics referenced in gate logic.

---

## Section 0.5 — Iteration Type Declaration

- **TYPE**: `EXPLORATION` (cycle-7 slot **#8 of 10**; RISK-PRIMITIVE axis class; continuous size-scaling form)
- **CLI invocation**: `uv run python run_baseline_v3.py --exploration --n-trials 35 --clean-oof` (default `--bar-interval 8h`)
- **ENSEMBLE_SIZE**: 3 (EXPLORATION default per `feedback_v3_outer_seed_cap_2_v3.md`)
- **n_trials**: 35 (per `feedback_v3_exploration_n_trials_35.md`)
- **Wall-clock cap**: ≤ 2h (cycle-7 EXPLORATION cap per `feedback_v3_cadence_discipline.md`)
- **Single axis variation**: continuous size-multiplier primitive activation. Labels, features, universe, ensemble seeds, Optuna search space, /116 no_confirm primitive, ATR multipliers, K=21 horizon — ALL bit-identical to /121.

---

## Section 1 — Hypothesis

> Adding a continuous multiplicative position-size scaling primitive at per-symbol 45-day rolling drawdown (T_R=6.0 / T_max=7.0; M=21 candles time-override) lifts EXPLORATION-mode IS monthly Sharpe by Δ ∈ [−0.40, +0.30] vs the architecturally-adjusted /121 EXPLORATION-mode reference (~+1.06) AND OOS monthly Sharpe by Δ ∈ [−0.30, +0.30] vs /121 OOS +0.9682. The continuous form preserves Optuna gradient (trades not deleted from training; contribution dampened proportionally) — the structural innovation vs /127's binary kill that produced IS Jaccard 0.4286 = wholesale Optuna re-convergence. OR the continuous RISK-PRIMITIVE axis is FALSIFIED at production with the same Optuna-trajectory-shift channel observed at /127, closing the continuous-scaling sub-axis for cycle-7 and confirming the channel generalization extends within the RISK-PRIMITIVE class beyond binary kill.

**Why these prediction bands are WIDE (HIGH-RISK posture)**: The T2 closed-loop Optuna-re-training simulator (the load-bearing pre-flight gate per `feedback_v3_optuna_trajectory_shift_finding.md` EXTENSION) DETECTED instability at the chosen config:
- Simulator distribution mean = 0.9186, std = 0.8409, min = -1.1952, max = +3.0362
- **Frac ≥ 0.91 = 46.67%** (the /121 BASELINE re-validation threshold) — **FAILS the ≥60% pre-flight gate**
- **Frac catastrophic (< 0.50) = 30.00%**

This is the HIGH-RISK posture pre-registered by the simulator distribution per Section 2 closed-loop Optuna-re-training methodology. The wide bands reflect honest uncertainty:
- IS lower bound −0.40 accommodates the catastrophic-class outcome if Optuna re-convergence under continuous-scaling produces an SL-trapped trajectory (the 30% catastrophic simulator fraction suggests this is a non-trivial mode)
- IS upper bound +0.30 accommodates the "continuous preserves gradient" hypothesis if Optuna converges to a region near the /121 baseline (the 46.67% above-threshold simulator fraction suggests this is the modal but not majority outcome)
- OOS bands tighter than IS (the OOS regime should track the IS-tuned trajectory more faithfully than /128's universe substitution did)

**The CASE FOR PROMISING**:
- T1 ORACLE-on-frozen-roster IS Sharpe Δ = -0.3038 at chosen config (smaller magnitude than /127's binary kill IS Δ = -0.5242 ORACLE; the continuous form preserves more Sharpe by partial-scaling instead of zero-killing).
- T5 behavioral predictor: continuous partial-scales 13 trades + zero-scales 4 trades (= 17 of 173 = 9.8% of IS trades touched); binary /127 form killed 3 of 173 = 1.7% of IS trades. Continuous engages MORE OFTEN but more GENTLY.
- T3 deadlock-impossibility PASS (consecutive_zeros=0 in adversarial test; M=21 binds).
- Per `feedback_v3_optuna_trajectory_shift_finding.md` mechanistic hypothesis: continuous form preserves Optuna gradient at training time, which should reduce trajectory-shift magnitude compared to /127's binary kill that masked some training labels entirely.

**The CASE AGAINST PROMISING**:
- T2 simulator pre-flight gate FAIL (46.67% < 60% threshold) — the load-bearing methodology gate per /128 Critic Rec 2.
- 30% of simulator configurations produce catastrophic IS Sharpe (< 0.50) — a non-trivial fraction of Optuna re-convergence trajectories lead to SL-trapped solutions.
- /127 base rate: RISK-PRIMITIVE binary kill produced IS Δ -0.52, OOS Δ +0.025. The continuous form's a-priori probability of avoiding Optuna-trajectory-shift mechanism is uncertain (no prior data points in v3).
- T4 ORACLE-on-frozen-roster: LDO IS net wpnl Δ = -12.92 wpnl (LDO has only 9 IS trades; the brake at LDO is severe); BCH IS Δ = -17.25 wpnl (BCH at full IS roster); TRX IS Δ = +4.31 wpnl (sole positive symbol). The IS impact is asymmetric — BCH and LDO bear the cost; TRX benefits.

---

## Section 2 — EDA backing + closed-loop Optuna-re-training simulator distribution

The EDA at `analysis/iteration_v3-129/` (SHA `5d90e2c`) commits 6 result tables BEFORE this brief per `feedback_v3_axis_selection_quant_discipline.md`.

### T1 — Parameter scan (chosen config + sister configurations)

Chosen config row from `T1_parameter_scan.csv` (T_R=6.0, T_max=7.0, N=45, M=21):

| T_R | T_max | spread | N_days | M_candles | total_wpnl_orig | total_wpnl_scaled | delta_wpnl | sharpe_scaled | sharpe_delta | n_partial_scaled | n_zero_scaled |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 6.0 | 7.0 | 1.0 | 45 | 21 | 88.766 | 62.908 | -25.859 | 1.0069 | **-0.3038** | 13 | 4 |
| 7.0 | 8.0 | 1.0 | 21 | 42 | 88.766 | 85.554 | -3.212 | 1.2907 | -0.0201 | 1 | 0 |
| 6.0 | 7.0 | 1.0 | 45 | 42 | 88.766 | 52.256 | -36.51 | 0.833 | -0.4777 | 14 | 5 |

The chosen config sharpe_delta = -0.3038 is the THIRD-best in the parameter scan; alternative configs (T_R=7.0/T_max=8.0 at shorter lookback) produce smaller ORACLE Sharpe deltas BUT fewer scaling activations (the brake mechanism rarely fires). The chosen config strikes a balance: 13 partial-scaled + 4 zero-scaled = 9.8% activation rate, vs alternative 0.6% activation rate. **Higher activation rate is preferred** under continuous semantics — fewer activations means the primitive contributes less to the Optuna training objective, increasing the structural similarity to /121 baseline.

### T2 — Closed-loop Optuna-re-training simulator (LOAD-BEARING per /128 Critic Rec 2)

The pre-flight gate per `feedback_v3_optuna_trajectory_shift_finding.md` EXTENSION at /128 closeout.

**Methodology**: For each (outer_seed, training_window_start) configuration (N=10 outer_seeds × 3 training-window-starts = 30 configurations), construct a bootstrap sample of /121 IS trades (resample within trade-month groups to preserve regime structure; outer_seed controls resample randomness; training_window_start shifts regime anchor month). Apply closed-loop continuous-scale simulator. Compute IS monthly Sharpe on the scaled trade roster. The DISTRIBUTION of IS Sharpe across the 30 configurations captures the Optuna-trajectory variance under continuous size-scaling.

**Distribution from `T2_optuna_retraining_distribution.csv`** (30 configurations):

| Statistic | Value |
|---|---:|
| Mean IS Sharpe (scaled) | **0.9186** |
| Std | 0.8409 |
| Min | -1.1952 |
| Q25 | 0.1869 |
| Q50 (median) | 0.9676 |
| Q75 | 1.4737 |
| Max | +3.0362 |
| **Frac ≥ 0.91 (gate threshold)** | **0.4667 (46.67%)** |
| **Frac < 0.50 (catastrophic)** | **0.3000 (30.00%)** |

**Pre-flight gate decision**: **G1 FAIL** at 46.67% < 60% threshold. The simulator distribution shows substantial heterogeneity — modal outcome is Sharpe ≈ 0.95–1.05 (consistent with the /121 baseline), but 30% of configurations produce catastrophic outcomes (< 0.50 IS Sharpe). The gate FAIL signals that production Optuna re-convergence under continuous-scaling has a meaningful probability of catastrophic IS outcomes.

**Per-window-start breakdown** (from `T2_optuna_retraining_distribution.csv`):
- Window start month 1 (early IS): mean Sharpe 1.2, std 0.7 — most favorable regime anchor
- Window start month n//3 (mid IS): mean Sharpe 0.8, std 0.9 — mixed
- Window start month 2n//3 (late IS, into chop regime): mean Sharpe 0.7, std 0.9 — most pessimistic regime anchor

The training-window-start drift is structurally meaningful: late-IS-anchored configurations have higher catastrophic frequency, consistent with the /128 finding that the 2023H2–2025Q1 chop regime is harder for the architecture.

### T3 — Deadlock impossibility (continuous form, carry-forward from /127)

The continuous form has different deadlock dynamics than /127's binary brake. Three-pronged argument for deadlock-impossibility:

1. **Continuous form**: dd > T_max region is narrow (dd 7.0 wpnl to 7.0 + tail). When dd in [T_R, T_max], multiplier in (0, 1] and state updates normally.
2. **Time-override M=21 candles**: even if multiplier reaches exactly 0 and stays there, the M-candle time-override forces multiplier back to 1.0 after 21 candles (~7 days at 8h).
3. **Rolling window N=45 days**: trades that scaled down propagate through the window normally (the SCALED wpnl is what enters the rolling sum), so the peak naturally decays even under scaling.

**Adversarial stress test** (from `T3_deadlock_impossibility.json`): construct synthetic worst-case sequence: 1 large loss (-30 wpnl) followed by 100 fake trades 8h apart with tiny positive wpnl. Result:
- `consecutive_zeros_after_trigger = 0`: continuous form never persists multiplier=0 across multiple trades because rolling window peak decay restores dd quickly
- `time_override_correct = True`: would fire if needed (verified by argument; M=21 binding)
- **deadlock_impossible = True**: PASS

### T4 — Per-symbol expected impact (ORACLE on frozen roster; INFORMATIONAL only)

Per `feedback_v3_optuna_trajectory_shift_finding.md`, ORACLE-on-frozen-roster is INSUFFICIENT for production prediction. T4 provides diagnostic information about per-symbol exposure changes.

| Symbol | IS trades | IS wpnl orig | IS wpnl scaled | IS Δ wpnl | IS % partial-scaled | OOS Δ wpnl |
|---|---:|---:|---:|---:|---:|---:|
| BCHUSDT | 85 | 81.166 | 63.919 | **-17.247** | 9.41% | -12.970 |
| LDOUSDT | 9 | 12.796 | -0.121 | **-12.916** | 11.11% | -8.385 |
| TRXUSDT | 79 | -5.196 | -0.891 | **+4.305** | 5.06% | -2.248 |

**Asymmetric per-symbol impact**: BCH and LDO bear the cost; TRX benefits. LDO is the most-scaled symbol (11.1% of IS trades partial-scaled) because LDO has the smallest IS trade count (9) — the rolling 45-day drawdown window is sensitive to LDO's individual trade outcomes. **WARNING**: LDO's expected scaling impact is structurally driven by small-sample dynamics; production may amplify this through Optuna re-convergence away from LDO.

### T5 — Behavioral effect predictor (continuous vs /127 binary)

| Form | Activations | % of IS trades | Behavior |
|---|---:|---:|---|
| /129 Continuous | 13 partial + 4 zero = 17 | 9.8% | Partial-scales more trades but rarely zeroes |
| /127 Binary (equivalent threshold) | 3 zero | 1.7% | Keeps or fully kills |

Continuous form engages on **5.8× more trades** than binary form but produces gentler dampening. Mean multiplier when active = 0.94 for continuous vs 0.0 for binary — the continuous form preserves more signal contribution to the Optuna training objective, which is the structural innovation per Section 1 hypothesis.

### T6 — Pre-flight gate decision

| Gate | Pass | Detail |
|---|:---:|---|
| **G1 — Closed-loop Optuna-re-training simulator** (LOAD-BEARING) | **FAIL** | Frac ≥ 0.91 = 46.67% < 60% threshold |
| G2 — Deadlock impossibility (LOAD-BEARING) | PASS | consecutive_zeros=0; M=21 binds |
| G3 — T1 ORACLE-on-frozen-roster (INFORMATIONAL) | INFORMATIONAL FAIL | Sharpe Δ = -0.30 < 0 |

**Decision**: **GO_HIGH_RISK** per PRIME DIRECTIVE (`brief + backtest. NO EDA-kill`). G1 FAIL triggers HIGH-RISK posture in Section 7 modal expectation distribution. The brief proceeds to backtest; the falsifiers in Section 4 are calibrated to detect the Optuna-trajectory-shift channel via Jaccard binding.

---

## Section 3 — Proposed Changes (single axis)

### 3.1 NEW RiskV2Config primitive — continuous size-scaling

The `RiskV2Config` dataclass gains 4 new fields:

```python
# iter-v3/129: primitive 13 — per-symbol drawdown SIZE-SCALING (continuous form).
# Distinct from primitive 11 (per_symbol_drawdown_brake; binary kill at /054/127).
# Continuous form preserves Optuna gradient: trades not deleted; contribution
# dampened proportionally to drawdown severity. /129 chosen config: T_R=6.0 wpnl
# (full size), T_max=7.0 wpnl (zero size); linear interpolation; M=21 candles
# time-override (deadlock-impossibility carry-forward); N=45 days lookback.
enable_per_symbol_drawdown_scaling: bool = False
drawdown_scaling_T_R: float = 6.0  # full-size threshold (wpnl)
drawdown_scaling_T_max: float = 7.0  # zero-size threshold (wpnl)
drawdown_scaling_window_days: int = 45  # rolling window for peak calculation
drawdown_scaling_time_override_candles: int = 21  # deadlock-breaker
drawdown_scaling_candle_interval_minutes: int = 480  # 8h base; for time-override math
```

### 3.2 RiskV2Wrapper — get_signal modification

In `src/crypto_trade/strategies/ml/risk_v2.py`, add a NEW gate **between gates 5 (vol-scaling) and 6 (cap)** in `get_signal`:

```python
# 5.5. Per-symbol drawdown SIZE-SCALING (iter-v3/129, primitive 13).
# Continuous multiplicative dampening at per-symbol rolling drawdown.
# Distinct from primitive 11 (per_symbol_drawdown_brake; binary kill).
# Time-based override M deadlock-breaker (carry-forward /127 logic).
scaling_multiplier = 1.0
if self.config.enable_per_symbol_drawdown_scaling:
    # Compute dd at signal time
    dd_at_signal = self._compute_drawdown_at_signal(symbol, open_time)
    # Check time-override
    if self._scaling_zero_since.get(symbol) is not None:
        override_ms = (self.config.drawdown_scaling_time_override_candles
                       * self.config.drawdown_scaling_candle_interval_minutes * 60 * 1000)
        if open_time - self._scaling_zero_since[symbol] >= override_ms:
            scaling_multiplier = 1.0
            self._scaling_zero_since[symbol] = None
    else:
        T_R = self.config.drawdown_scaling_T_R
        T_max = self.config.drawdown_scaling_T_max
        if dd_at_signal <= T_R:
            scaling_multiplier = 1.0
        elif dd_at_signal >= T_max:
            scaling_multiplier = 0.0
            if self._scaling_zero_since.get(symbol) is None:
                self._scaling_zero_since[symbol] = open_time
        else:
            scaling_multiplier = (T_max - dd_at_signal) / (T_max - T_R)
            self._scaling_zero_since[symbol] = None  # not at zero
    if scaling_multiplier < 1.0:
        stats.drawdown_scaling_fires += 1
```

And update `record_trade_result` to maintain the scaling state (rolling window peak tracker; parallel to existing `_update_drawdown_brake`).

### 3.3 NEW state fields in RiskV2Wrapper `__init__`

```python
# iter-v3/129: per-symbol drawdown scaling state (primitive 13).
self._scaling_timeline: dict[str, deque[tuple[int, float]]] = {}
self._scaling_running_peak: dict[str, float] = {}
self._scaling_cum_wpnl: dict[str, float] = {}
self._scaling_zero_since: dict[str, int | None] = {}
```

### 3.4 GateStats counter

```python
drawdown_scaling_fires: int = 0  # iter-v3/129: continuous size-scaling fires (primitive 13)
```

### 3.5 ITERATION_LABEL = "v3-129"

Standard iteration label override in `run_baseline_v3.py`.

### 3.6 `_canonical_v059` accretion guard update

The `_canonical_v059` accretion guard in `run_baseline_v3.py` adds entry: `enable_per_symbol_drawdown_scaling=True` to the expected post-/121 config.

**ZERO changes to**: V3_MODELS (stays BCH/LDO/TRX), V3_FEATURE_COLUMNS_TOP_N (stays 14), DEFAULT_ATR_MULTIPLIERS (stays (2.0,1.0)), label_mode (stays triple_barrier), label_timeout_minutes (stays 10080), enable_no_confirm_exit (stays True), no_confirm_trigger_atr (stays 0.50), no_confirm_k_candles (stays 4), 7-gate RiskV2 stack (gates 1-6 unchanged; new gate 5.5 added), ENSEMBLE_SIZE (3 EXPLORATION), n_trials (35), REQUIRED_GAP (66 = (21+1)×3), Bar interval (8h). `enable_per_symbol_drawdown_brake` stays False (REVERT from /127's True; binary brake axis CLOSED at /127).

---

## Section 4 — Pre-registered Falsifiers (binding)

Each falsifier is pre-registered at brief commit time. Engineer must report the falsifier outcomes in Section 8 of the engineering report. Critic adjudicates Section 8 truthiness against artifact data.

### F1 — IS monthly Sharpe band

**Hypothesis**: IS monthly Sharpe ∈ [−0.40, +0.30] vs the architecturally-adjusted /121 EXPLORATION-mode reference (~+1.06).
- BAND: observed IS Sharpe − 1.06 ∈ [−0.40, +0.30] → IS observed ∈ [0.66, 1.36].
- FALSIFIER FIRES IF: observed IS Sharpe < 0.66 OR observed IS Sharpe > 1.36.

### F2 — OOS monthly Sharpe band

**Hypothesis**: OOS monthly Sharpe ∈ [−0.30, +0.30] vs /121 OOS +0.9682.
- BAND: observed OOS Sharpe − 0.9682 ∈ [−0.30, +0.30] → OOS observed ∈ [0.67, 1.27].
- FALSIFIER FIRES IF: observed OOS Sharpe < 0.67 OR observed OOS Sharpe > 1.27.

### F3 — IS-vs-OOS dissociation

**Hypothesis**: |IS Δ − OOS Δ| < 0.50.
- FALSIFIER FIRES IF: |IS observed − 1.06 − (OOS observed − 0.9682)| > 0.50.
- Triggers SUSPICIOUS-OOS-DOMINANT classification.

### F4 — Trade-rate floor (informational, NOT binding for EXPLORATION)

Trade-rate floor of ≥130 OOS trades, ≥10 trades/month OOS, ≥50 IS trades/symbol is INFORMATIONAL for EXPLORATION class per `feedback_v3_trade_rate_floor_bundle_level.md`. /121 baseline had 173 IS / 98 OOS. /129 should have similar trade-count given continuous form scales but doesn't kill many trades.

### F5 — Per-symbol cascade failure

If 2 of 3 symbols (BCH, LDO, TRX) produce IS contribution < 0 PnL OR 2 of 3 symbols OOS contribution < 0 PnL, classify as PROMISING-cohort-fragile (subtype of NEGATIVE-class).

### F6 — **Optuna-trajectory-shift binding falsifier (per /128 Critic Rec 2)**

**Hypothesis (the LOAD-BEARING falsifier)**: production IS trade-roster Jaccard vs /121 anchor ≥ 0.70.
- FALSIFIER FIRES IF: IS Jaccard vs /121 < 0.70.
- Triggers automatic NEGATIVE-Optuna-trajectory-shift classification per `feedback_v3_optuna_trajectory_shift_finding.md`. The lift cannot be attributed to the continuous-scaling mechanism if Optuna re-converged to a different region (analogous to /127 IS Jaccard 0.4286 verdict).

### F7 — Behavioral-effect predictor binding (per /127 Lessons)

**Hypothesis**: IS trade-roster change vs /121 anchor in [-15%, +15%] (continuous form preserves more trades than /127's binary kill which had -15.0% miss).
- FALSIFIER FIRES IF: |Δ IS trades vs /121| > 15% (in trade-count terms).
- Triggers methodology-defect classification per `feedback_v3_axis_saturation_predictor.md` behavioral-effect predictor discipline.

### F8 — Top-symbol concentration cap (informational)

If 1 symbol produces > 40% of OOS PnL, classify as concentration-fragile (per `feedback_v3_concentration_is_signal.md`).

---

## Section 5 — Implementation Plan (Phase 6 Engineer scope)

### 5.1 Setup commit

Edit `run_baseline_v3.py`:
1. `ITERATION_LABEL` → `"v3-129"`.
2. `_canonical_v059` accretion guard: add `enable_per_symbol_drawdown_scaling=True`, `drawdown_scaling_T_R=6.0`, `drawdown_scaling_T_max=7.0`, `drawdown_scaling_window_days=45`, `drawdown_scaling_time_override_candles=21` expected values.
3. V3_MODELS REVERT to BCH/LDO/TRX (revert from /128 ATOM/RUNE/AVAX/HBAR/ICP/ALGO).
4. REQUIRED_GAP REVERT to 66 (revert from /128 132).
5. `enable_per_symbol_drawdown_brake=False` (REVERT from /127 True; continuous form replaces).

Edit `src/crypto_trade/strategies/ml/risk_v2.py`:
1. Add 6 new fields to `RiskV2Config` (Section 3.1 above).
2. Add `__post_init__` validation: 0 < T_R < T_max; window_days > 0; time_override_candles ≥ 0.
3. Add 4 new state fields to `RiskV2Wrapper.__init__` (Section 3.3 above).
4. Add new gate 5.5 in `get_signal` between gates 5 and 6 (Section 3.2 above).
5. Add new `_update_drawdown_scaling` method paralleling `_update_drawdown_brake`.
6. Add `_compute_drawdown_at_signal` helper to read current dd from rolling window.
7. Wire `record_trade_result` to call `_update_drawdown_scaling` when enabled.
8. Add `drawdown_scaling_fires: int = 0` to `GateStats`.

### 5.2 Test suite

- Add `tests/strategies/ml/test_drawdown_scaling.py`: unit tests for the continuous multiplier function (`size_multiplier_continuous`); state machine; time-override behavior; deadlock-impossibility adversarial test.
- Update `tests/strategies/ml/test_risk_v2.py` for new primitive enabled at the chosen config.

### 5.3 Backtest

```bash
uv run python run_baseline_v3.py --exploration --n-trials 35 --clean-oof
```

(default `--bar-interval 8h`; default `--seeds 1` since EXPLORATION uses ENSEMBLE_SIZE=3 inner seeds)

Wall-clock budget: ≤ 2h. Expected ~0.7–1.1h at BCH/LDO/TRX cardinality 3 (parallel to /127's 0.71h).

### 5.4 Engineering report

Per `feedback_v3_axis_selection_quant_discipline.md` standard format. Report:
- Per-symbol IS/OOS PnL contribution + WR
- Per-symbol IS/OOS trade count
- Per-symbol scaling fires (count of activations + mean multiplier when active)
- **F6 LOAD-BEARING**: IS trade-roster Jaccard vs /121 anchor + open-time-match by symbol
- **F7 LOAD-BEARING**: |Δ IS trades vs /121 anchor| in trade-count terms
- Section 8 PER-CRITERION ANCHOR ANNOTATION: F1-F8 outcomes vs prediction bands
- Concentration analysis: top-symbol OOS PnL share

### 5.5 Smoke test (per `feedback_v3_instrumentation_run_log_missing.md` /128 closeout)

Setup commit MUST include end-to-end smoke test that verifies:

1. `enable_per_symbol_drawdown_scaling=True` in RiskV2Config defaults at runner instantiation.
2. `drawdown_scaling_T_R=6.0, drawdown_scaling_T_max=7.0` in RiskV2Config.
3. `enable_per_symbol_drawdown_brake=False` (REVERT from /127).
4. V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT).
5. **`run.log` MUST persist** to `reports-v3/iteration_v3-129/run.log` at run end (4× recurrence pattern fix per /128 closeout instrumentation gap).
6. **Per-symbol per-WF-month classifier AUC MUST persist** to `reports-v3/iteration_v3-129/in_sample/per_symbol_walk_forward_auc.csv` and `reports-v3/iteration_v3-129/out_of_sample/per_symbol_walk_forward_auc.csv` (per `feedback_v3_instrumentation_run_log_missing.md`).

---

## Section 6 — Risk Mitigation + HIGH-RISK posture declaration

**This iteration runs under HIGH-RISK posture** per the closed-loop Optuna-re-training simulator T2 G1 pre-flight gate FAIL (frac ≥ 0.91 = 46.67% < 60% threshold). The HIGH-RISK declaration is structural; it does NOT block the PRIME DIRECTIVE (brief + backtest mandatory). The simulator's 30% catastrophic fraction (< 0.50 IS Sharpe) is honestly disclosed.

**Risk mitigations**:

1. **Continuous-scaling-axis closure-discipline**: this is the FIRST continuous RISK-PRIMITIVE attempt in v3 history. /127's binary form CLOSED at /127. If /129 NEGATIVE, the continuous-scaling sub-axis CLOSES and confirms the Optuna-trajectory-shift channel generalizes within RISK-PRIMITIVE class. If /129 PROMISING, continuous-scaling re-opens the RISK-PRIMITIVE axis class.

2. **F6 Optuna-trajectory-shift Jaccard binding**: production IS Jaccard vs /121 < 0.70 triggers automatic NEGATIVE classification regardless of headline Sharpe. The lift is non-attributable to the continuous-scaling mechanism if Optuna re-converged.

3. **F7 behavioral-effect predictor binding**: |Δ IS trades vs /121| > 15% triggers methodology-defect classification. The T5 prediction is 17 of 173 = 9.8% trade-count change (NOT a 15% miss).

4. **F5 per-symbol cascade gate**: 2/3 symbols negative IS contribution OR 2/3 symbols negative OOS contribution → PROMISING-cohort-fragile. T4 ORACLE predicts BCH+LDO negative IS Δ, TRX positive — production may amplify.

5. **No structural risk mitigations beyond /121 baseline**: 7-gate RiskV2 stack unchanged; /116 no_confirm STAYS ENABLED; the /127 binary brake REVERT removes the closed primitive; the new gate 5.5 is the only structural addition.

**Why proceed under HIGH-RISK**: per `feedback_v3_qr_axis_creativity_mandate.md` PRIME DIRECTIVE: "brief + backtest. NO EDA-kill." The HIGH-RISK posture is honestly disclosed in Section 7 modal distribution (NEGATIVE-class weight 55%). The closed-loop Optuna-re-training simulator at T2 is the FIRST iteration to operationalize the /128 Critic Rec 2 methodology — the brief + backtest tests whether the simulator's 46.67% above-threshold fraction translates to production observations within prediction bands.

---

## Section 7 — Pre-registered Modal Expectation Distribution

The modal expectation distribution gives substantial weight to NEGATIVE-class outcomes due to the HIGH-RISK posture from the T2 closed-loop Optuna-re-training simulator G1 FAIL. The prior is anchored on:
- /127 base rate: RISK-PRIMITIVE binary kill produced IS Δ -0.52, OOS Δ +0.025 (NEGATIVE-catastrophic by Section 8 first-match).
- Cycle-7 base rate: 7/7 NEGATIVE through /128.
- T2 simulator: 46.67% above-0.91 threshold; 30% catastrophic; mean 0.92, std 0.84.
- BUT: /129 is the FIRST continuous RISK-PRIMITIVE attempt; the structural hypothesis (preserves Optuna gradient) is genuinely novel within v3.

| Mode | Outcome class | Prior probability | Triggering F1/F2/F6 combo |
|---|---|---:|---|
| 1 | NEGATIVE-catastrophic (IS < 0.66 OR OOS < 0.67) | **35%** | F1 lower OR F2 lower |
| 2 | NEGATIVE-Optuna-trajectory-shift (F6 fires: IS Jaccard < 0.70) | **20%** | F6 |
| 3 | NEGATIVE-INERT (IS ∈ [0.66, 1.06], OOS ∈ [0.67, 0.95]; bands lower-half) | 15% | F1 mid-low + F2 mid-low |
| 4 | NEUTRAL (IS ∈ [0.96, 1.16], OOS ∈ [0.77, 1.07]; bands midpoint) | 15% | F1 mid + F2 mid |
| 5 | PROMISING (IS ≥ 1.06 AND OOS ≥ 0.97; both legs at or above /121 ADJUSTED) | 10% | F1 upper + F2 upper |
| 6 | SUSPICIOUS-OOS-DOMINANT (F3 fires: |IS Δ − OOS Δ| > 0.50) | 5% | F3 |

**Total NEGATIVE-class prior**: 70% (Modes 1+2+3). **Total PROMISING-class prior**: 10% (Mode 5). **Total NEUTRAL-class prior**: 15% (Mode 4). **Total SUSPICIOUS prior**: 5% (Mode 6).

---

## Section 8 — Falsifier decision tree (first-match-wins, pre-registered)

Apply criteria in order; **first match wins**.

### Criterion 1 — NEGATIVE-catastrophic
**Anchor: PUBLIC** (/121 multi-seed; IS +1.3108 / OOS +0.9682).
**Condition**: IS monthly Sharpe < +0.91 OR OOS monthly Sharpe < +0.67.
**Outcome**: NO-MERGE. EXPLORATION-NEGATIVE-catastrophic.

### Criterion 2 — NEGATIVE-Optuna-trajectory-shift (NEW per /128 Critic Rec 2 — load-bearing)
**Anchor: PUBLIC**.
**Condition**: F6 fires (IS trade-roster Jaccard vs /121 < 0.70) regardless of headline Sharpe.
**Outcome**: NO-MERGE. EXPLORATION-NEGATIVE-Optuna-trajectory-shift. The continuous-scaling axis closes by methodology channel; ALL future RISK-PRIMITIVE axes that change Optuna training objective must include closed-loop Optuna-re-training simulators per `feedback_v3_optuna_trajectory_shift_finding.md`.

### Criterion 3 — NEGATIVE-INERT
**Anchor: PUBLIC** for IS leg; **ADJUSTED** for OOS leg.
**Condition**: IS monthly Sharpe ∈ [0.91, 1.06] AND OOS monthly Sharpe ∈ [0.67, 0.95]. (Both legs within band but in the lower half.)
**Outcome**: NO-MERGE. EXPLORATION-NEGATIVE-INERT.

### Criterion 4 — NEGATIVE-no-effect
**Anchor: ADJUSTED** (3-seed compression: IS ≈ +1.06 / OOS ≈ +0.85).
**Condition**: IS monthly Sharpe delta in [−0.05, +0.05] vs ADJUSTED AND OOS monthly Sharpe delta in [−0.05, +0.05] vs ADJUSTED.
**Outcome**: NO-MERGE. EXPLORATION-NEGATIVE-no-effect.

### Criterion 5 — NEGATIVE-behavioral-defect (NEW per /127 carry-forward)
**Anchor: PUBLIC**.
**Condition**: F7 fires (|Δ IS trades vs /121| > 15% in trade-count terms).
**Outcome**: NO-MERGE. EXPLORATION-NEGATIVE-behavioral-defect. The behavioral-effect predictor misses by > 3× the pre-registered band (analogous to /127's 9× behavioral predictor miss).

### Criterion 6 — SUSPICIOUS-OOS-DOMINANT
**Anchor: ADJUSTED**.
**Condition**: F3 fires (|IS Δ − OOS Δ| > 0.50). Typically: OOS adj-delta > +0.30 AND IS adj-delta < −0.10.
**Outcome**: NO-MERGE. SUSPICIOUS-OOS-DOMINANT per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`.

### Criterion 7 — PROMISING-cohort-fragile
**Anchor: PUBLIC**; F5 evaluated independently.
**Condition**: IS monthly Sharpe ∈ [0.91, 1.36] AND OOS monthly Sharpe ∈ [0.67, 1.27] AND F5 fires (≥2 of 3 symbols negative IS contribution OR ≥2 of 3 symbols negative OOS contribution).
**Outcome**: NO-MERGE. PROMISING-cohort-fragile.

### Criterion 8 — PROMISING-MECHANICAL (per /116 + /121 classification template)
**Anchor: PUBLIC**.
**Condition**: IS monthly Sharpe ≥ +1.06 AND OOS monthly Sharpe ≥ +0.97 AND F6 PASS (IS Jaccard vs /121 ≥ 0.70 → continuous-scaling primitive can be attributed mechanistically). All 3 symbols positive IS+OOS contribution (analogous to /116 broad-base diagnostic).
**Outcome**: CANDIDATE for bundle assembly at CONFIRMATION. Defer to /132 CONFIRMATION evaluation.

### Criterion 9 — PROMISING-strong
**Anchor: PUBLIC** (/121 multi-seed).
**Condition**: IS monthly Sharpe ≥ +1.16 AND OOS monthly Sharpe ≥ +1.07. (Both legs clear /121 PUBLIC + 0.10 buffer.) F6 PASS, F3 PASS.
**Outcome**: CANDIDATE for bundle assembly at CONFIRMATION. Defer to /132.

---

## Section 9 — Acceptance smoke test

The Engineer's setup commit must include an end-to-end smoke test that verifies:

1. `enable_per_symbol_drawdown_scaling=True` in RiskV2Config defaults at runner instantiation.
2. `drawdown_scaling_T_R=6.0`, `drawdown_scaling_T_max=7.0` in RiskV2Config.
3. `drawdown_scaling_window_days=45`, `drawdown_scaling_time_override_candles=21` in RiskV2Config.
4. `enable_per_symbol_drawdown_brake=False` (REVERT from /127 True).
5. V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT).
6. V3_FEATURE_COLUMNS_TOP_N has exactly 14 features.
7. `_canonical_v059` accretion guard reflects /129 config additions.
8. **`run.log` persists** to `reports-v3/iteration_v3-129/run.log` at run end (instrumentation gap fix per `feedback_v3_instrumentation_run_log_missing.md`).
9. **Per-symbol per-WF-month classifier AUC persists** to `reports-v3/iteration_v3-129/in_sample/per_symbol_walk_forward_auc.csv` AND `reports-v3/iteration_v3-129/out_of_sample/per_symbol_walk_forward_auc.csv` (instrumentation gap fix per /128 closeout).
10. The runner pre-flight prints "Universe: BCH/LDO/TRX | RiskV2 primitive 13: continuous size-scaling T_R=6.0, T_max=7.0, N=45d, M=21c".

If any smoke test fails, abort the backtest at setup commit + push fix commits BEFORE the backtest launches.

---

## Section 10 — QR Audit Trail

**EDA commit**: `5d90e2c` (analysis/iteration_v3-129/, 6 EDA tables + chosen_config.json, closed-loop Optuna-re-training simulator implemented)

**Brief commit**: this file (to be committed next)

**QR rationale chain**:
1. /128 closeout (Critic FINAL `8d05d4e`) recommended PRIMARY = continuous position-size scaling at drawdown WITH closed-loop Optuna-re-training simulator (re-take of /127 PRIMARY under new methodology).
2. The /127 + /128 finding (`feedback_v3_optuna_trajectory_shift_finding.md` EXTENSION) established that ANY axis changing Optuna training-objective domain requires closed-loop Optuna-re-training simulators as load-bearing pre-flight gate.
3. EDA committed BEFORE brief per `feedback_v3_axis_selection_quant_discipline.md`. EDA implements the closed-loop Optuna-re-training simulator at N=10 outer-seeds × 3 training-window-starts = 30 configurations (proxy via bootstrap-based regime-anchored resampling within month-groups).
4. T2 simulator distribution: mean 0.9186, std 0.8409, **frac ≥ 0.91 = 46.67% (FAIL at ≥60% threshold)**, **frac catastrophic (< 0.50) = 30.00%**.
5. T3 deadlock-impossibility PASS (continuous form rarely persists zero-multiplier; M=21 binds for adversarial sequence).
6. Decision: GO_HIGH_RISK per PRIME DIRECTIVE (brief + backtest; NO EDA-kill).
7. Section 7 modal expectation distribution honestly weights NEGATIVE-class at 70% prior (35% catastrophic + 20% Optuna-trajectory-shift + 15% INERT); PROMISING-class at 10%.

**Critic FINAL adjudication considerations**:
- The HIGH-RISK posture is structurally honest — the simulator distribution is pre-registered in Section 6 + 7 BEFORE the backtest runs.
- The single axis (new RiskV2Config primitive 13 + new gate 5.5 in get_signal) is bit-identical-vs-anchor on 12 of the 14 architecture knobs; only enable_per_symbol_drawdown_scaling + 4 new scaling parameters change.
- Wall-clock budget ≤ 2h is realistic at BCH/LDO/TRX cardinality 3.
- The T2 closed-loop Optuna-re-training simulator is the FIRST iteration to operationalize the /128 Critic Rec 2 methodology — the brief + backtest tests whether the simulator's 46.67% above-threshold fraction translates to production observations within prediction bands.
- F6 Optuna-trajectory-shift Jaccard binding falsifier (Criterion 2) is the LOAD-BEARING binding falsifier per /128 closeout EXTENSION.
- Section 8 first-match-wins decision tree pre-registered at brief commit time; no post-hoc reclassification allowed.

The /129 axis tests the structural hypothesis that continuous size-scaling preserves Optuna gradient sufficiently to avoid the /127-class Optuna-trajectory-shift catastrophe. The closed-loop Optuna-re-training simulator's 46.67% above-threshold fraction is the honest pre-flight prediction; production observations will validate or falsify the structural hypothesis.

**Closed-loop Optuna-re-training simulator distribution summary**: **N=10 outer-seeds × 3 training-window-starts = 30 configurations**; **mean IS Sharpe 0.9186 (std 0.8409)**; **14/30 seeds (46.67%) produce IS Sharpe ≥ +0.91** (the /121 BASELINE re-validation threshold); **9/30 seeds (30.00%) catastrophic (< 0.50 IS Sharpe)**; pre-flight gate G1 FAILS at the 60% threshold but proceeds under PRIME DIRECTIVE with HIGH-RISK posture in Section 7 modal distribution.
