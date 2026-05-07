# Iteration v3-022 — Research Brief

**Type**: EXPLORATION (cadence #4 of 10 in the post-bootstrap cycle; **STRUCTURAL axis (Category 4 — NEW risk primitive: regime-conditional kill switch)** — first regime-conditional gate primitive in v3 catalog per `feedback_v3_iter019_axis_priorities.md` MEDIUM #4 ELEVATED per Critic FINAL `f5b89a3` of iter-v3/021)
**Track**: v3 (rigor arm) — twenty-second iteration
**Branch**: `iteration-v3/022` (off `iteration-v3/021` head; analysis commit `b728313` shipped before this brief)
**Date**: 2026-05-07
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE (shared across v1, v2, v3)
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 1              # SET BY --exploration
ensemble_seeds   = _derive_ensemble_seeds(outer_seed, size=1)
n_trials         = 35             # SET BY --exploration default (iter-v3/020 establishment; PRELIMINARY-VALIDATED through iter-v3/021)
colsample_bytree = 1.0            # HARDCODED by --exploration
OOS_CUTOFF_MS    = 1742774400000  # millisecond representation
```

**Sacred constants UNCHANGED.** The QR sees OOS metrics for the FIRST time in Phase 7. This brief is produced reading ONLY: iter-v3/007–021 briefs / engineering reports / Critic / diaries; iter-v3/022 EDA `analysis/iteration_v3-022/regime_gate_eda.py` outputs (committed at SHA `b728313` BEFORE this brief). The EDA reads ONLY pre-OOS-cutoff IS-window kline data for threshold calibration; OOS-window data is NOT consulted at any point. iter-v3/018 IS trades.csv is read (for counterfactual reference) but contaminates nothing — the IS partition is mechanical at `OOS_CUTOFF_MS`.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION (cadence #4 of 10 post-bootstrap)
Wall-clock budget: < 30 min target / 2h hard cap
Single-axis variation: NEW risk primitive — regime-conditional kill switch
                       on TRX position-taking when (a) BTC drawdown_30d > 20%
                       OR (b) |BTC vol_zscore_30d| > 1.5
                       per Critic FINAL Rec #1 of iter-v3/021 (SHA `f5b89a3`) +
                       iter-v3/021 diary `Pre-Commit for iter-v3/022` section
Cadence: EXPLORATION #4 of 10 needed before next CONFIRMATION (earliest = iter-v3/029)
Axis category: 4 (NEW risk primitive — regime-conditional kill switch;
               MEDIUM #4 ELEVATED to within-cycle HIGH per iter-v3/021 closeout)
ANCHOR: iter-v3/018 BOOTSTRAP baseline (multi-seed mean +0.3788 IS / +0.3869 OOS)
NOT a gate-threshold knob (this is a NEW gate primitive, not tuning an existing one).
NOT a feature-pruning variation. NOT a feature-add variation. NOT a labeling change.
NOT a model architecture change. NOT a universe-expansion (reverts iter-v3/021 5→3).
This iteration NEVER updates BASELINE_V3.md.
```

**Justification — STRUCTURAL regime-gate axis (per `feedback_v3_iter019_axis_priorities.md` LOCKED MEDIUM #4 ELEVATED per iter-v3/021 Critic FINAL `f5b89a3` + `feedback_v3_concentration_is_signal.md` LOCKED orthogonal mechanism category #iv binary off/on)**:

After iter-v3/021 EXPLORATION-NEGATIVE clean (universe expansion HBAR+AVAX failed; Critic FINAL SHA `f5b89a3`, diary commit `92290fd`):

- The HBAR+AVAX universe-expansion attempt is **CLOSED at the catalog level** for the current 10-EXPLORATION cycle. EDA correlation captured price-level diversity NOT signal diversity in the 13-feature space; HBAR+AVAX both deeply negative IS+OOS (-85.7% combined IS PnL drag).
- Per `feedback_v3_concentration_is_signal.md` LOCKED 2026-05-07: structural axes touching concentration MUST use orthogonal mechanisms. The 4 permitted alternatives are (i) universe expansion (CLOSED-symbols-cycle at iter-v3/021), (ii) per-symbol drawdown brake, (iii) vol-target ceiling, (iv) **regime-conditional kill switch (binary off/on)** — iter-v3/022 axis = mechanism (iv).
- iter-v3/022 axis = MEDIUM-priority #4 (TRX/2022-Q4 regime gate), ELEVATED to within-cycle HIGH per Critic FINAL `f5b89a3` of iter-v3/021. Per the catalog discipline that ALL outstanding-constraint axes should be tested before any retesting of speculative axes — iter-v3/022 is a SURGICAL structural fix addressing BASELINE_V3.md outstanding constraint #5 (PBO max=1.0 on TRX/2022-10 + TRX/2023-01 — FTX/LUNA crash regime).
- Forward priority order from `feedback_v3_iter019_axis_priorities.md`:
  1. ~~HIGH — NEW feature families (iter-v3/019)~~ — closed for cycle (PROMISING-INERT)
  2. ~~HIGH — Concentration architecture sub-axis A (per-symbol cap, iter-v3/020)~~ — CLOSED-mechanism (NEGATIVE clean / PATH C)
  3. ~~HIGH — Concentration architecture sub-axis B (universe expansion, iter-v3/021)~~ — CLOSED-symbols-cycle (NEGATIVE clean)
  4. **HIGH (ELEVATED from MEDIUM) — TRX/2022-Q4 regime gate (iter-v3/022 mandate)** — current iteration
  5. MEDIUM — DSR gate reformulation
  6. MEDIUM — Funding rate retest at n_trials=35
  7. LOW — Knob axes (saturated)

**iter-v3/022 first EXPLORATION axis = HIGH-priority (ELEVATED from MEDIUM #4) — TRX/2022-Q4 regime gate.** Cannot be renegotiated post-hoc per the LOCKED priority order + LOCKED concentration-mechanism rule.

**Why regime-gate axis NOW (post iter-v3/021 NEGATIVE)**:

- BASELINE_V3.md outstanding constraint #5 (PBO max=1.0 on TRX/2022-10 + TRX/2023-01) is a structural failure of iter-v3/018's CONFIRMATION methodology — neither universe expansion (iter-v3/021) nor per-symbol cap (iter-v3/020) addressed it. Both axes operated at the symbol/concentration layer, not the regime layer.
- The TRX cells with PBO=1.0 are concentrated in the FTX/LUNA crash regime (Oct 2022 + Jan 2023 train_month windows). A regime-conditional kill switch is the SURGICAL mechanism — it suppresses candidate signals only when BTC is in regime-stress, leaving normal-regime training data fully intact.
- Single-axis discipline preserved: ONE new gate primitive added (regime-aware kill on TRX); existing 7 risk gates unchanged; 13 V3_FEATURE_COLUMNS unchanged; 3-symbol BCH+LDO+TRX universe (revert iter-v3/021's 5-symbol expansion).

**Why TRX-only and not portfolio-level regime gate**:

- The high-PBO cells are TRX-specific (TRX/2022-10, TRX/2023-01 are PBO=1.0; BCH/LDO have no PBO≥0.99 cells). Per-symbol architecture means the regime-gate primitive can be TRX-targeted without affecting BCH/LDO model fits.
- Portfolio-level regime gate would suppress BCH/LDO during the same windows; that's a more aggressive change without IS evidence motivating it. The brief stays single-axis on TRX-only regime kill.

After iter-v3/022 the catalog will have: features × 2 + labeling × 1 + gate-zscore × 1 + gate-btc-trend × 1 + universe × 2 (drop-MKR retention + expand-to-5 NEGATIVE) + gate-adx × 1 (CLOSED) + NEW microstructure feature × 1 (CLOSED-narrow) + NEW model arch × 1 (CLOSED-at-config) + NEW labeling arch × 1 (PATH C) + bootstrap CONFIRMATION × 1 + NEW external-data-source feature × 1 (PROMISING-INERT) + NEW risk primitive (per-symbol cap) × 1 (CLOSED-mechanism) + NEW universe expansion × 1 (CLOSED-symbols-cycle) + **NEW risk primitive (regime-conditional kill switch on TRX) × 1** = 14 unique axis representations after iter-v3/022, **first regime-conditional gate primitive in v3 catalog**.

---

## Section 1 — Hypothesis

Adding a regime-conditional kill switch to RiskV2Wrapper that suppresses TRX position-taking signals when (a) BTC drawdown_30d > 20% over 30 days, OR (b) |BTC vol_zscore_30d| > 1.5 (calibrated against IS-window 90th/95th-percentile distributions per EDA SHA `b728313` synthesis.md), with thresholds and logical-OR composition LOCKED at brief authoring, will **reduce PBO at the high-PBO TRX cells (TRX/2022-10 PBO=1.0; TRX/2023-01 PBO=1.0) without removing edge from normal-regime training data**, because the gate operates at the per-bar candidate-signal layer (not the trade-execution layer): Optuna's per-cell hyperparameter search at iter-v3/018 n_trials=50 was unstable in the FTX/LUNA regime (high-PBO cells), partly because the optimization could fit hyperparameters that selected for "trades during regime stress" — pruning those bars makes the cell's IS Sharpe more stable, lowering PBO. Predicted IS Sharpe band [+0.32, +0.50] median +0.41 (anchor +0.38; bands tightly clustered around anchor because the gate fires concentrated on TRX's already-negative-IS regime windows; small positive lift expected from removing the noisiest cells); predicted OOS Sharpe band [+0.40, +0.55] median +0.47 (anchor +0.39; small lift expected from PBO methodology improvement); predicted PBO mean band [0.10, 0.13] (anchor 0.0892); predicted PBO max band [0.6, 0.85] (anchor 1.0; reduction is the primary success metric).

**Mechanism explanation** (why regime-gate should help PBO without destroying IS Sharpe): in iter-v3/018's BOOTSTRAP CONFIRMATION, the TRX cells in 2022-10 + 2023-01 had PBO=1.0 because the per-cell CPCV walk-forward measured high IS-Sharpe instability across n_trials=50 hyperparameter configurations. The instability arises because in the FTX/LUNA crash regime, BTC volatility spikes drive cross-asset correlation breakdowns — features that normally have stable cross-asset relationships (e.g., zscore_logvolume_30, fracdiff_logclose_dstat) shift to non-stationary regimes. Optuna's hyperparameter search fits the MOST sensitive trees in those windows, producing high in-sample Sharpe with high variance across hyperparameter configs (= high PBO). Suppressing candidate signals in regime-stress bars (gate fires at calibrated 14.49% IS-wide rate, concentrated in FTX/LUNA + COVID + LUNA-Celsius-3AC) removes the noisy training material from those cells; Optuna's search converges on more robust hyperparams; IS Sharpe within those cells stabilizes; PBO drops.

**Why the gate may NOT lift OOS Sharpe** (3 PATH-C-suspect scenarios):
1. **PATH C-1: Gate over-filters TRX**, removing too many positive-PnL trade entries in normal regimes. IS-wide kill rate at calibrated thresholds = 1.3% (1 trade of 75); per-bar fire rate = 14.49%. The brief expects this to be conservative, but Optuna at n_trials=35 split 3 ways may compensate by fitting hyperparams that emit MORE trades elsewhere — degrading per-trade economics if the new entries are lower-quality.
2. **PATH C-2: Gate is REGIME-MISALIGNED with OOS**. The OOS window 2025-03-24 onward may have BTC regime profiles unlike the FTX/LUNA training-window precedent — if 2025-Q3 / 2026-Q1 hit the gate criteria for unrelated reasons (e.g., normal-cycle correction), the gate kills profitable trades. EDA cannot test this directly (OOS-blind); the brief Section 6 falsifier 3 falsifies if OOS gate-fire rate > 25% (i.e., gate fires on more than 25% of OOS bars, indicating regime-misalignment).
3. **PATH C-3: Optuna at n_trials=35 cannot stably re-optimize TRX hyperparams under the new constraint**. The gate effectively shrinks TRX's training data by 14.49% (in BAR count, not trade count); per-symbol Optuna budget = 35 trials × 1 inner × 1 outer = 35 fits per cell on the reduced training set. If the reduction destabilizes Optuna's path, IS Sharpe degrades.

The counterfactual evidence (Section 2) shows that under iter-v3/018 IS, the calibrated gate fires at non-trivial rates in BOTH PBO=1.0 cells (TRX/2022-10 at 11.8%; TRX/2023-01 at 38.7% — exceeds the gate-fire-rate-zero null), and the IS-wide trade-entry kill rate is small (1.3%) preserving the bulk of TRX's normal-regime training data. The empirical question this EXPLORATION answers is whether the per-cell PBO measurement stabilizes in those high-PBO cells, AND whether OOS Sharpe is maintained (not degraded by the constraint).

---

## Section 2 — IS-Only Numerical Evidence + Behavioral-Effect Predictor

**EDA script**: `analysis/iteration_v3-022/regime_gate_eda.py` (committed at SHA `b728313` BEFORE this brief — Phase 5.5 reproducibility requirement).

**Inputs read** (IS-only window 2020-01-01 → 2025-03-24):
- `data/BTCUSDT/8h.csv` — 5,727 IS bars (BTC kline data; spot index for regime gate)
- `reports-v3/iteration_v3-018/in_sample/trades.csv` — 75 TRX IS trades (for counterfactual reference)
- `reports-v3/iteration_v3-018/per_cell_pbo.csv` — 60 TRX (symbol, train_month) cells (for PBO correlation)

**Outputs** (committed alongside the script at SHA `b728313`):
- `analysis/iteration_v3-022/btc_regime_profile_2022q4.csv` — per-month BTC DD% / |vol z| / gate-fire rate in 2022-09 to 2023-03 target window
- `analysis/iteration_v3-022/trx_counterfactual_kills.csv` — per-month TRX trade kills + PnL impact
- `analysis/iteration_v3-022/per_month_pbo_correlation.csv` — TRX per-cell PBO joined with gate-fire rate per training month
- `analysis/iteration_v3-022/threshold_calibration.csv` — 5×5 threshold grid sweep (DD ∈ {15, 18, 20, 22, 25}%, vol_z ∈ {1.0, 1.25, 1.5, 1.75, 2.0})
- `analysis/iteration_v3-022/synthesis.md` — narrative + locked threshold rationale

### 2.1 Honest threshold calibration (load-bearing)

**The user-prompted thresholds in the iter-v3/022 axis prior (BTC drawdown_30d > 30% OR BTC vol_zscore > 2.5) DO NOT FIRE in the 2022-Q4 FTX/LUNA window.** Empirical IS-window distribution evidence:

| Metric | Mean | Median | 75th pct | 90th pct | 95th pct | 98th pct | 99th pct | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTC drawdown_30d | 9.4% | 7.1% | 13.7% | 20.6% | 27.6% | 35.9% | 38.8% | 54.1% |
| BTC \|vol_zscore_30d\| | 0.64 | 0.54 | 0.87 | 1.29 | 1.55 | 1.79 | 2.07 | 15.03 |

The naive thresholds (DD > 30%, |vol_z| > 2.5) trigger only the top ~3% of bars (DD) and top ~0.5% of bars (vol_z). In 2022-Q4 specifically, peak BTC drawdown_30d was **26.3%** (Nov 2022, FTX peak) — BELOW the 30% threshold. Peak |vol_zscore_30d| was **1.65** (Jan 2023) — BELOW 2.5. The naive thresholds were intuition-based, not data-calibrated.

**Calibrated thresholds (LOCKED for iter-v3/022 implementation per EDA `b728313`)**:
- DD threshold: **20.0%** (IS-90th-percentile = 20.6%; small buffer below)
- |vol z-score| threshold: **1.5** (IS-95th-percentile = 1.55; small buffer below)
- Logical OR: gate fires when DD > 20% OR |vol_z| > 1.5

This calibration is conservative — both thresholds at the high-but-not-extreme tail of the IS distribution. Gate fires concentrated on regime-stress periods (FTX-peak Nov 2022 at 92.2% bar-fire rate, March 2020 COVID at 74.2%, May 2021 China-ban at 60.2%, May/June 2022 LUNA-Celsius-3AC at 60.2-74.2%) without blanket-killing TRX trades in normal regimes.

### 2.2 BTC regime profile in 2022-Q4 / 2023-Q1 (target window)

| Month | n_bars | max DD% | max \|vol_z\| | gate-fire bars | fire rate |
|---|---:|---:|---:|---:|---:|
| 2022-09 | 90 | 24.5% | 0.84 | 18 | 20.0% |
| 2022-10 | 93 | 14.9% | 1.61 | 11 | 11.8% |
| 2022-11 | 90 | 26.3% | 1.64 | **83** | **92.2%** |
| 2022-12 | 93 | 21.0% | 1.57 | 18 | 19.4% |
| 2023-01 | 93 | 8.5% | 1.65 | 36 | 38.7% |
| 2023-02 | 84 | 9.6% | 1.06 | 0 | 0.0% |
| 2023-03 | 93 | 20.9% | 0.63 | 4 | 4.3% |

Gate fires concentrated on FTX-peak (2022-11 at 92.2%) and on BOTH high-PBO TRX cells (2022-10 at 11.8%, 2023-01 at 38.7%). Both DD and vol_z components contribute: 2022-10 + 2022-11 + 2022-12 + 2023-01 all had peak |vol_z| > 1.5; 2022-09 + 2022-11 + 2022-12 + 2023-03 all had peak DD > 20%.

### 2.3 Counterfactual: TRX trades killed in target window (iter-v3/018 IS)

| Month | n_TRX_trades | n_killed | kill rate | PnL total | PnL killed | PnL kept |
|---|---:|---:|---:|---:|---:|---:|
| 2022-10 | 2 | 0 | 0.0% | +5.5373 | 0.0000 | +5.5373 |
| 2022-11 | 1 | 1 | 100.0% | 0.0000 | 0.0000 | 0.0000 |
| 2022-12 | 0 | 0 | — | 0.0000 | 0.0000 | 0.0000 |
| 2023-01 | 1 | 0 | 0.0% | 0.0000 | 0.0000 | 0.0000 |
| 2023-02 | 6 | 0 | 0.0% | -6.1926 | 0.0000 | -6.1926 |

The November 2022 trade is the only target-window kill (FTX-collapse week). The trade had 0.0 weighted_pnl (model entered but neither TP nor SL fired before timeout) — net PnL impact of the kill = 0.

**Counterfactual kill count for iter-v3/018 Q4 2022: 1 TRX trade killed** (the single trade that opened during the FTX-peak 92.2% gate-fire month).

### 2.4 IS-wide kill statistics

- Total IS TRX trades (iter-v3/018): **75**
- Total killed at calibrated thresholds: **1** (1.3% IS kill rate)
- IS-wide gate fire rate (all bars): **14.49%** (830 of 5,727 IS bars)
- Per-trade kept PnL: -7.3262 vs total -7.3262 (kept = total within rounding; PnL preservation 1.000)
- IS-wide bar-level kills: 830 of 5,727 bars (14.49%) — operates at per-bar candidate-signal level, not just trade-entry level

The gate's primary effect is **at the per-bar Optuna training-data layer**, not the trade-execution layer. By suppressing 14.49% of training bars (concentrated on FTX/LUNA + COVID + May/June 2022), the gate reshapes the IS feature distribution Optuna sees during hyperparameter optimization. The per-trade kill count (1 of 75) is incidental — most TRX trade entries are during normal-regime windows.

### 2.5 Per-cell PBO correlation: high-PBO cells overlap with gate-fire bars

| TRX cell | PBO | gate-fire rate (training month) | max DD% | max \|vol z\| |
|---|---:|---:|---:|---:|
| TRX/2022-10 | **1.000** | 11.8% | 14.9% | 1.61 |
| TRX/2023-01 | **1.000** | 38.7% | 8.5% | 1.65 |

**Both** PBO=1.0 cells have non-trivial gate-fire activity in their training month (the cells where outstanding constraint #5 lives are exactly the cells where the gate is designed to operate). Their gate-fire rates differ — TRX/2022-10 has 11.8% (driven by the few high-vol_z bars in that month); TRX/2023-01 has 38.7% (driven by sustained vol_z elevation post-FTX). The mechanism the brief is testing — that suppressing candidate signals during regime-stress reduces the per-cell PBO — has direct empirical overlap with the cells that anchor BASELINE_V3.md outstanding constraint #5.

### 2.6 Behavioral-effect predictor (per `feedback_axis_saturation_predictor.md`)

The gate fires on 14.49% of IS bars. Predicting the IS trade-count change for iter-v3/022 vs iter-v3/018 anchor (both 3-symbol BCH+LDO+TRX universe; iter-v3/018 anchor IS = 172 multi-seed mean trade count):

- **TRX trades expected to drop by 1-2** in iter-v3/022 vs anchor (calibrated direct kill = 1; small adjustment for Optuna re-optimization removing ~1 more trade in nearby windows where the gate fired but no anchor trade existed).
- **BCH + LDO trades unchanged** by mechanism design (gate is TRX-specific).
- Predicted IS trade band: **[170, 175]** (anchor 172; ±3 trades; saturation falsifier band ±10% = [155, 189]).
- Behavioral-effect predictor pre-commit: if observed IS trades < 155 (axis over-fires) OR > 189 (axis propagates beyond design), saturation falsifier fires.
- Note: the gate operates at per-bar candidate-signal level, so per-symbol Optuna may absorb some of the gate's effect via hyperparameter shift; the saturation band ±10% accounts for this.

### 2.7 Setup integrity (verified at SHA `b728313`)

- ✅ EDA script committed BEFORE brief (Phase 5.5 requirement) — `b728313` precedes this brief commit
- ✅ All EDA outputs (CSVs + synthesis.md) committed in same commit
- ✅ Past-only discipline verified: BTC drawdown_30d uses 90-bar trailing peak with `.shift(1)`; vol_zscore_30d uses cumulative IS-mean/std up to t-1 (expanding-window with `.shift(1)`); per-trade kill check uses `np.searchsorted(side='left') - 1` (current bar excluded)
- ✅ OOS-window data NOT consulted at any step
- ✅ Threshold calibration was on IS distribution percentiles (90th / 95th), not OOS Sharpe target

---

## Section 3 — Proposed Changes

### 3.1 Symbols — REVERT iter-v3/021's universe expansion (5 → 3)

```
V3_MODELS = (
    ("A (BCHUSDT)", "BCHUSDT"),
    ("C (LDOUSDT)", "LDOUSDT"),
    ("D (TRXUSDT)", "TRXUSDT"),
)  # iter-v3/022: revert iter-v3/021's HBAR+AVAX expansion (closed at catalog level)
```

REQUIRED_GAP back from 110 → **66 = (21 + 1) × 3** (formula: (timeout_candles + 1) × n_symbols). Runtime assertion `_verify_label_leakage_gap()` re-asserts.

### 3.2 Labeling — UNCHANGED (iter-v3/010 ATR 2.0/1.0)

`atr_tp = 2.0`, `atr_sl = 1.0`, `timeout_candles = 21` — byte-identical to iter-v3/018 anchor. NO labeling axis variation in this iteration.

### 3.3 Features — UNCHANGED 13 V3_FEATURE_COLUMNS

`funding_rate_zscore_30` ABSENT (iter-v3/019 PROMISING-INERT close); `tbr_zscore_30` ABSENT (iter-v3/015 INERT close); `vwap_dev_50` ABSENT (iter-v3/008 redundancy close). 13 V3_FEATURE_COLUMNS byte-identical to iter-v3/018 anchor. NO feature axis variation in this iteration.

KEEP `funding_v3.py` module + `crypto-trade fetch-funding` CLI + `data/funding_rates/<sym>.csv` cache infrastructure (zero revert cost; preserves option for iter-v3/028+ CONFIRMATION retest).

### 3.4 Risk gates — ADD ONE NEW PRIMITIVE; existing 7 gates unchanged

NEW gate primitive 9 (sister to primitive 8 per-symbol cap): **regime-conditional kill switch on TRX**.

```python
@dataclass(frozen=True)
class RiskV2Config:
    ...
    # iter-v3/022: regime-conditional kill switch (primitive 9)
    # Gate fires when EITHER:
    #   (a) BTC drawdown_30d > regime_dd_threshold_pct (default 20.0%)
    #   (b) |BTC vol_zscore_30d| > regime_vol_zscore_threshold (default 1.5)
    # Calibrated against IS-window 90th/95th-pct (EDA b728313 synthesis.md).
    # Targets: TRX-only by default (iter-v3/022 single-axis); other symbols
    # opt-in via regime_gate_symbols.
    enable_regime_gate: bool = False
    regime_gate_symbols: tuple[str, ...] = ()  # e.g., ("TRXUSDT",)
    regime_dd_lookback_bars: int = 90  # 30 calendar days at 8h cadence
    regime_dd_threshold_pct: float = 20.0  # IS-90th-pct + small buffer
    regime_vol_lookback_bars: int = 90  # 30 calendar days at 8h cadence
    regime_vol_zscore_threshold: float = 1.5  # IS-95th-pct
```

Implementation: `RiskV2Wrapper._build_lookups` populates a per-bar `_btc_regime_lookup` array (BTC drawdown_30d + vol_zscore_30d, computed past-only at lookup-build time). At trade-signal candidate evaluation, if `symbol in regime_gate_symbols` AND (drawdown > threshold OR |vol_z| > threshold), the signal is killed (`weight_factor = 0.0`). Past-only enforcement: BTC drawdown / vol z-score computed from BTC 8h kline data with strict timestamp < t discipline.

iter-v3/022 runtime config (loaded by `run_baseline_v3.py`):
```python
RISK_CONFIG = RiskV2Config(
    ...
    enable_regime_gate=True,
    regime_gate_symbols=("TRXUSDT",),
    regime_dd_threshold_pct=20.0,
    regime_vol_zscore_threshold=1.5,
)
```

### 3.5 Sub-fix decomposition (7-item; one per first-commit pre-commit per iter-v3/021 diary `Pre-Commit for iter-v3/022`)

1. **DROP HBARUSDT + AVAXUSDT from V3_MODELS** (revert iter-v3/021's 5 → 3). Verifies via `len(V3_MODELS) == 3` + spot-check on (BCH, LDO, TRX) tuple membership.
2. **REQUIRED_GAP back 110 → 66 = (21 + 1) × 3**. Update `validation_v3.REQUIRED_GAP` constant; `_verify_label_leakage_gap()` runtime assertion confirms at runtime.
3. **Add `regime_gate` config fields to RiskV2Config** (default disabled outside this iteration). 6 new fields per Section 3.4 spec.
4. **Implement BTC drawdown_30d + vol_zscore_30d tracker in RiskV2Wrapper._build_lookups**. Past-only via `.shift(1)`; cumulative IS-mean/std uses `expanding(min_periods=...)` masked by `is_mask`.
5. **ITERATION_LABEL = "v3-022"** in `run_baseline_v3.py`.
6. **Per-symbol cap stays disabled** (iter-v3/020 closed it; KEEP infrastructure at zero revert cost). `enable_per_symbol_cap=False` in runtime config.
7. **Adversarial test for past-only discipline on regime gate** — new test `tests/strategies/ml/test_regime_gate_past_only.py`: verifies that the gate at bar `t` cannot peek at BTC bar `t` data; only bars with `open_time < t.open_time` contribute. Asserts via constructed adversarial fixture.

### 3.6 Brief-vs-Code reconciliation table (Phase 5.5 input) — 12 verifiers

| # | Verifier | Brief Section | Code Site (planned) |
|---|---|---|---|
| 1 | V3_MODELS = 3 (BCH, LDO, TRX) | §3.1 | `run_baseline_v3.py` `V3_MODELS` tuple |
| 2 | REQUIRED_GAP = 66 = (21+1)×3 | §3.1 | `validation_v3.REQUIRED_GAP` constant + runtime assert |
| 3 | V3_FEATURE_COLUMNS = 13 (UNCHANGED) | §3.3 | `_verify_feature_columns()` runtime assert |
| 4 | enable_regime_gate=True | §3.4 | runtime `RISK_CONFIG` + RiskV2Config field |
| 5 | regime_gate_symbols=("TRXUSDT",) | §3.4 | runtime `RISK_CONFIG` + RiskV2Config field |
| 6 | regime_dd_threshold_pct=20.0 | §3.4 | runtime `RISK_CONFIG` + RiskV2Config field |
| 7 | regime_vol_zscore_threshold=1.5 | §3.4 | runtime `RISK_CONFIG` + RiskV2Config field |
| 8 | enable_per_symbol_cap=False | §3.5 #6 | runtime `RISK_CONFIG` |
| 9 | ITERATION_LABEL="v3-022" | §3.5 #5 | `run_baseline_v3.py` line 102 |
| 10 | EXPLORATION mode (--exploration --seeds 1) | §0 | CLI args at runtime |
| 11 | n_trials=35, colsample_bytree=1.0 | §0 | EXPLORATION mode default |
| 12 | Past-only discipline for regime gate | §3.5 #7 | `tests/strategies/ml/test_regime_gate_past_only.py` |

### 3.7 NO labeling/feature-prune/universe-expansion/gate-knob changes

All other strategy parameters byte-identical to iter-v3/018 anchor:
- ATR labeling 2.0/1.0
- 13 V3_FEATURE_COLUMNS unchanged
- 3-symbol BCH+LDO+TRX universe
- 7-primitive risk gate stack (vol scaling, ADX, Hurst, z-score OOD, low-vol filter, hit-rate-OFF, BTC trend filter ±15%)
- zscore_threshold=2.0, adx_threshold=20.0, btc_trend_threshold_pct=15.0

The single-axis variation is the addition of primitive 9 (regime-conditional kill switch on TRX); everything else is byte-identical.

### 3.8 Inheritance from iter-v3/021 closeout

- Per-symbol cap infrastructure KEPT (zero revert cost); cap stays DISABLED.
- Funding rate infrastructure KEPT (zero revert cost); funding_rate_zscore_30 stays ABSENT from V3_FEATURE_COLUMNS.
- HBAR+AVAX universe expansion REVERTED (5 → 3).
- sklearn pin (>=1.8,<1.9) inherited from iter-v3/020.
- n_trials=35 EXPLORATION default inherited from iter-v3/020 (PRELIMINARY-VALIDATED through iter-v3/021).

---

## Section 4 — Expected OOS Impact

### 4.1 EXPLORATION → headline metrics are GUIDANCE not GATES

EXPLORATION-mode metrics are INFORMATIONAL per `feedback_v3_dsr_mode_artifact.md`. The brief's predicted bands are guidance for falsifier construction; only CONFIRMATION-mode metrics enter MERGE gate evaluation.

### 4.2 Predicted IS / OOS Sharpe ranges

| Metric | Anchor (iter-v3/018 multi-seed mean) | Predicted iter-v3/022 (single-seed EXPLORATION) | Predicted Δ |
|---|---:|---:|---:|
| IS monthly Sharpe | +0.3788 | **[+0.32, +0.50]** median +0.41 | -0.06 to +0.12 |
| OOS monthly Sharpe | +0.3869 | **[+0.40, +0.55]** median +0.47 | +0.01 to +0.16 |
| IS n_trades | 172 (mean) | **[170, 175]** median 172 | 0 to ±3 |
| OOS n_trades | 90.5 (mean) | **[85, 95]** median 90 | 0 to ±5 |
| IS MaxDD | 21.86% | maintained or slightly improved | ±2pp |
| OOS MaxDD | 27.74% | maintained or slightly improved | ±3pp |
| PBO mean | 0.0892 | **[0.10, 0.13]** | ±0.04 |
| PBO max | 1.0 | **[0.6, 0.85]** | -0.40 to -0.15 (PRIMARY success metric) |
| n_eff | 25 (CONFIRMATION) | **[15, 22]** | EXPLORATION regime |

**PBO max reduction is the primary success metric** for iter-v3/022. The gate is structurally targeted at the PBO=1.0 cells, and the EDA evidence shows non-trivial gate-fire activity in BOTH cells. A PBO max drop from 1.0 to <0.85 demonstrates the mechanism is operating as designed; a drop to <0.6 would be exceptional.

### 4.3 Falsifiers (locked before backtest)

| # | Falsifier | Threshold | Trigger condition | Verdict on fire |
|---|---|---|---|---|
| 1 | NEGATIVE indicator | OOS Sharpe Δ < -0.10 from anchor +0.3869 | Observed OOS < +0.2869 | NEGATIVE clean (single-axis fail) |
| 2 | PROMISING indicator | Within predicted IS band [+0.32, +0.50] AND OOS Sharpe Δ > +0.10 | Both conditions met | PROMISING |
| 3 | OOS regime-misalignment | OOS gate fire rate > 25% | Gate over-fires in OOS | NEGATIVE; gate is regime-misaligned (PATH C-2) |
| 4 | PBO methodology lift | PBO max drops below 0.85 in TRX cells | TRX/2022-10 + TRX/2023-01 PBO < 0.85 | PROMISING-METHODOLOGY |
| 5 | Saturation falsifier | IS trades NOT in [155, 189] | Observed IS trades < 155 or > 189 | NEGATIVE; axis behavior unexpected |
| 6 | Trade-rate floor (informational) | OOS trades < 130 at single-seed | Below 130 at EXPLORATION | INFORMATIONAL caveat (per `feedback_trade_rate_floor`) |
| 7 | NEGATIVE-no-effect (NULL-RESULT) | Trade roster bit-identical to iter-v3/018 anchor (172 IS, 90 OOS) AND IS Sharpe Δ < -0.10 | All three identity conditions met | NEGATIVE-no-effect (axis didn't propagate) |

### 4.4 EXPLORATION outcome interpretation (pre-commit catalog framing)

| Outcome | Catalog row framing | Bundle status |
|---|---|---|
| All falsifiers PASS + IS within band + OOS lift + PBO max drop | EXPLORATION-PROMISING-METHODOLOGY | Strong CONFIRMATION candidate (PBO methodology fix is rare) |
| Falsifier 2 fires (PROMISING) but PBO max unchanged | EXPLORATION-PROMISING-INERT-METHODOLOGY | Not a CONFIRMATION candidate; mechanism didn't operate at PBO layer |
| Falsifier 1 fires AND non-bit-identical roster AND axis propagated | EXPLORATION-NEGATIVE (clean) | NOT a CONFIRMATION candidate |
| Falsifier 7 fires (bit-identical roster) | EXPLORATION-NEGATIVE-no-effect (NULL-RESULT) | Not a CONFIRMATION candidate; gate didn't propagate |
| Falsifier 3 fires (OOS regime-misalignment) | EXPLORATION-NEGATIVE-PATH-C2 | Not a CONFIRMATION candidate; gate misaligned to OOS regime |
| Falsifier 5 fires (saturation) | EXPLORATION-NEGATIVE (axis behavior unexpected) | Not a CONFIRMATION candidate |

---

## Section 5 — Risk Mitigation

### 5.1 Cadence-discipline structural safeguards (5 inherited + 4 axis-specific = 9 total)

Inherited:
1. Single-axis variation discipline (only primitive 9 + V3_MODELS revert)
2. Sacred constants UNCHANGED (OOS_CUTOFF_DATE, training_months)
3. ITERATION_LABEL discipline (= "v3-022")
4. EXPLORATION wall-clock cap 2h (per `feedback_v3_cadence_discipline.md`)
5. Phase 5.5 reproducibility (EDA committed BEFORE brief at `b728313`)

Axis-specific:
6. Past-only discipline on BTC drawdown / vol_zscore (verified via adversarial test)
7. IS-only threshold calibration (90th / 95th percentile breakpoints; OOS-blind)
8. Gate fires only on TRX (not blanket portfolio kill); BCH/LDO unaffected
9. Calibrated thresholds documented in EDA SHA + brief Section 2.1; user-prompted naive thresholds explicitly identified as not-fitting-the-data

### 5.2 Methodology-pipeline safety (inherited from iter-v3/006-021)

- All 12 standard methodology checks (look-ahead, embargo width, multiple testing, IC correlation, ADF stationarity, Pareto dominance, reproducibility, hypothesis-implementation alignment, symbol exclusion, feature isolation, forming-candle audit, library version pinning) MUST PASS at Phase 7.5 Critic review.
- REQUIRED_GAP recompute at brief-time (66 for 3-sym universe).
- sklearn pin >=1.8,<1.9 (inherited from iter-v3/020).
- ENSEMBLE_SIZE=1 + colsample_bytree=1.0 EXPLORATION mode discipline.

### 5.3 NEW-gate-primitive-axis-specific risks (4 explicit)

1. **PATH C-1 risk (over-filter in normal regimes)**: gate at calibrated 1.3% trade-entry kill rate; brief Section 2.4 evidence is conservative. Falsifier 5 saturation [155, 189] catches axis over-firing.
2. **PATH C-2 risk (OOS regime-misalignment)**: brief Section 4.3 falsifier 3 (OOS gate fire rate > 25%) catches misalignment.
3. **PATH C-3 risk (Optuna search-budget destabilization)**: gate shrinks training data by 14.49% IS-wide; n_trials=35 split 3-way budget = 35 fits/symbol may not stably re-converge. Falsifier 1 catches IS Sharpe degradation.
4. **Threshold-calibration risk (chosen at IS percentiles)**: thresholds chosen on IS distribution, but the EDA does NOT optimize thresholds for any OOS Sharpe target. Calibration discipline disclosed in §2.1.

---

## Section 6 — Risk Management Design

The iter-v3/022 risk-management design adds primitive 9 (regime-conditional kill switch on TRX) without modifying the existing 7 primitives. The full v3 risk gate stack at iter-v3/022:

| # | Primitive | Status | Threshold |
|---|---|---|---|
| 1 | Vol scaling | ENABLED | floor 0.3, ceiling 1.0 |
| 2 | ADX gate | ENABLED | 20.0 |
| 3 | Hurst regime check | ENABLED | percentile band [0.05, 0.95] |
| 4 | Z-score OOD | ENABLED | 2.0 |
| 5 | Low-vol filter | ENABLED | atr_pct_rank_200 < 0.33 |
| 6 | Hit-rate gate | DISABLED | (per iter-v2/045 lesson) |
| 7 | BTC trend filter | ENABLED | ±15% over 14 days |
| 8 | Per-symbol PnL cap | DISABLED (iter-v3/020 closed) | — |
| **9** | **Regime-conditional kill switch (TRX-only)** | **ENABLED** (NEW) | **DD > 20% OR \|vol_z\| > 1.5** |

The stack is LARGER than iter-v3/018 by exactly one primitive. The single-axis discipline says only one primitive's parameters change per EXPLORATION; iter-v3/022's "change" is the addition of a new primitive at default-enabled state for TRX with calibrated thresholds.

---

## Section 7 — Pre-Registered Failure-Mode Prediction (5 predictions calibrated against 13 prior EXPLORATIONs + iter-v3/018 multi-seed evidence + iter-v3/022 EDA counterfactual)

| # | Prediction | Probability | Falsifier |
|---|---|---:|---|
| P1 | IS Sharpe within [+0.32, +0.50] | 50% | NEGATIVE clean if outside |
| P2 | OOS Sharpe within [+0.40, +0.55] | 35% | NEGATIVE clean if outside |
| P3 | PBO max drops below 0.85 in TRX cells | 50% | PROMISING-METHODOLOGY if both PBO=1.0 cells improve |
| P4 | OOS gate-fire rate < 25% | 65% | NEGATIVE-PATH-C2 if > 25% |
| P5 | IS trades within [155, 189] saturation band | 70% | NEGATIVE saturation if outside |

P1 + P2 cumulative probability ≈ 17.5% (joint); P1 + P2 + P3 cumulative ≈ 8.75% (the "best-case" outcome). P4 individually 65% — most likely OOS regime-alignment passes. P5 individually 70% — saturation band conservative.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Criteria — 8 EXPLORATION criteria

| # | Criterion | Threshold | Source |
|---|---|---|---|
| 1 | EXPLORATION verdict outcome | Falsifier 1/3/5/7 NOT fire | §4.3 + §4.4 |
| 2 | Methodology checks 1-12 | All PASS at Phase 7.5 Critic | inherited |
| 3 | EDA committed BEFORE brief | TRUE (SHA `b728313` < this brief commit) | Phase 5.5 |
| 4 | Reproducibility stamp | All 4 SHAs (Setup, gate, brief, EDA) recorded | inherited |
| 5 | Single-axis discipline | Only primitive 9 + V3_MODELS 5→3 revert + ITERATION_LABEL | §3.7 |
| 6 | Past-only audit | Adversarial test passes (test_regime_gate_past_only) | §5.3 |
| 7 | Calibrated thresholds documented | (DD=20, vol_z=1.5) explicit in §2.1 + EDA synthesis.md | §2.1 |
| 8 | Catalog row pre-commit | Locked in §11 below | §11 |

EXPLORATION does NOT enter MERGE evaluation. iter-v3/022 NEVER updates BASELINE_V3.md. Only CONFIRMATION can update.

---

## Section 9 — Library Stack Declaration

Pinned via `pyproject.toml` (inherited from iter-v3/020):

- Python 3.13+
- lightgbm = 4.6.0
- optuna = 4.8.0
- numpy = 2.2.6
- pandas = 3.0.0
- scikit-learn >= 1.8, < 1.9
- scipy = 1.17.0
- statsmodels = 0.14.6
- pyarrow = 23.0.1

Engineering report Phase 6 will record exact runtime versions for reproducibility audit.

---

## Section 10 — Adversarial Tests (one new test mandatory)

**NEW test file**: `tests/strategies/ml/test_regime_gate_past_only.py`

```python
def test_regime_gate_past_only():
    """Verify regime gate at bar t cannot peek at BTC bar t data.
    
    Adversarial fixture:
    - 100 bars of synthetic BTC data with a SINGLE regime-stress spike
      at bar t=50.
    - Build RiskV2Wrapper with regime gate enabled.
    - At bar t=50 (the spike bar itself), the gate should NOT fire — 
      the past-only discipline means the gate only sees data up to t=49.
    - At bar t=51, the gate SHOULD fire — the spike at t=50 is now in
      the rolling-DD/vol-z window.
    
    Asserts:
    - gate.fires_at(t=50) == False (spike not yet in past)
    - gate.fires_at(t=51) == True (spike now in past)
    - gate.fires_at(t=49) == False (no spike in past)
    """
```

The test is a regression guard against silent .shift() drops or `searchsorted(side='right')` bugs that would let the gate peek at the current bar.

---

## Section 11 — Catalog Row Pre-Commit (audit-trail discipline)

Per `feedback_v3_cadence_discipline.md` LOCKED. Pre-committed catalog row format (locked at brief authoring; engineering report will populate the actual numbers post-backtest):

```
| iter-v3/022 | 2026-05-MM | NEW risk primitive: regime-conditional kill switch on TRX (DD>20% OR |vol_z|>1.5) (MEDIUM #4 ELEVATED) | Δ TBD (vs iter-v3/018 anchor +0.3788) | TBD (vs anchor +0.3869) | EXPLORATION-{verdict TBD} | TBD — depending on PBO max change at high-PBO TRX cells |
```

Catalog caveats to be appended:
- Verdict-classification distinction: PROMISING-METHODOLOGY (PBO max drops below 0.85 at high-PBO TRX cells) is a NEW catalog subtype, distinct from PROMISING (general OOS lift). PBO methodology improvement without IS/OOS Sharpe lift = PROMISING-METHODOLOGY-INERT (sister to PROMISING-INERT).
- Threshold calibration discipline: thresholds chosen on IS-90th/95th-percentile distribution, NOT optimized for OOS Sharpe. Future regime-gate retests (different symbols, different lookback windows) inherit calibration discipline.
- TRX/2022-Q4 axis: closes if PBO max drops below 0.85 (mechanism worked); reopens if PBO max stays at 1.0 (mechanism didn't work) for either alternative thresholds OR alternative implementations (e.g., portfolio-level regime gate vs TRX-only).

The catalog row will be filled in Phase 8 diary closeout based on actual backtest outcomes. The pre-commit ensures the catalog framing is locked BEFORE results are known, preventing post-hoc rationalization.

---
