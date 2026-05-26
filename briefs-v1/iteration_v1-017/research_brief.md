# iter-v1/017 — Research Brief

**Iteration**: iter-v1/017 (CYCLE-3 EXPLORATION #2 of 10)
**Date**: 2026-05-26
**Branch**: `iteration-v1/017` (from `iteration-v1/016` HEAD `34e8960` + tag `v0.v1-016`)
**Axis family**: `universe` (UNUSED since /006; never in cycle-2 or cycle-3)
**Verdict-class**: EXPLORATION
**Author**: QR (Phases 1-5)

---

## Section 0 — Audit Header

### 0.1 Anchor

- BASELINE_V1.md `v0.v1-baseline-corrected` (`f8bc12c`) — IS Sharpe **+0.2829** / OOS Sharpe **+0.6637**
- Cycle-3 EXPLORATION ledger: 1 closed (/016 EXPLORATION-NEGATIVE catastrophic; sample-weighting axis CLOSED)
- BASELINE UNCHANGED through cycle-2 (10 NO-MERGE) and cycle-3 #1 (NO-MERGE)

### 0.2 Wall-clock estimate

- **Predicted**: 60 min (linear scaling from /016 50-min anchor; 6-sym × n_trials=18 × ENSEMBLE_SIZE=3)
- **Cap**: 2h EXPLORATION (per `feedback_v1_wall_clock_discipline_enforced.md`)
- **Margin**: 50% (well above the 20% Phase 5.5 floor)
- **Sub-linear realistic estimate** (per /016 LESSON #5 — 2× over-conservative): ~42 min; 65% margin

Detailed scenarios in `analysis/iteration_v1-017/wall_clock_scenarios.csv`.

### 0.3 Track detection

TRACK = v1; iteration NNN = 017; cycle position = 3-#2 (second cycle-3 EXPLORATION)

### 0.4 Boot files read

1. `ITERATION_PLAN_8H_V1.md` (v1 workflow)
2. `BASELINE_V1.md` (anchor + cycle-2 outcomes + cycle-3 ledger)
3. `briefs-v1/iteration_v1-016/{research_brief.md, lgbm_advisor.md (Phase 4.5 + 7.4), review.md, critic_preflight.md}`
4. `reports-v1/iteration_v1-016/engineering_report.md` (cycle-3 #1 closeout summary)
5. `diary-v1/iteration_v1-016.md` (5 LESSONS: abs_pnl structural, wiring≠edge, n_eff two-driver, ETH 3-axis drag, wall-clock conservative)
6. `briefs-v1/iteration_v1-006/research_brief.md` — prior universe iteration (NEGATIVE-DEGEN; MKR dead-feed defect)
7. `briefs-v1/exploration_catalog.md` (16 iterations to date; cycle-3 ledger)
8. `feedback_v1_wall_clock_discipline_enforced.md` (NON-NEGOTIABLE 2h cap)
9. `feedback_v1_abs_pnl_weighting_structural.md` (NEW from /016 closeout — sample-weighting axis CLOSED)
10. `feedback_v1_n_eff_barrier_magnitude_curve.md` (cycle-2 closure; label-shape + weight-distribution two-driver model)
11. `src/crypto_trade/features_v1/__init__.py` (V1_EXCLUDED_SYMBOLS, V1_BASELINE_UNIVERSE, V1_FEATURE_COLUMNS_PRUNED)
12. `run_baseline_v1.py:1148-1224` (current symbol dispatch: baseline 4-model OR fallback single-pooled)

### 0.5 Cycle/cadence position

**CYCLE-3 EXPLORATION #2 of 10**. Cycle-3 began at /016. CONFIRMATION earliest /026 per cycle-3 ledger.

### 0.6 Architecture-Family Justification (v1-only)

- **Axis family**: `universe` (UNUSED in cycle-3; UNUSED since /006 NEGATIVE-DEGEN cycle-2 first iteration)
- **Prior 5 EXPLORATION families** (from `briefs-v1/exploration_catalog.md` cycle-2/cycle-3 ledger):
  - iter-v1/012: `methodology-substrate-test`
  - iter-v1/013: `methodology-substrate-test`
  - iter-v1/014: `labeling`
  - iter-v1/015: `labeling` (CONFIRMATION)
  - iter-v1/016: `sample-weighting` (cycle-3 #1)
- **Rotation status**: **VALID** — `universe` is in NONE of the prior 5 families. Required per cycle-3 §0.6 rotation discipline + Critic /016 Path Forward #1 + LM Master Phase 7.4 §6 PRIMARY recommendation.
- **One-sentence rationale**: After /016 closed `sample-weighting` at the row-weight level (`uniform` mode catastrophic; `abs_pnl` structural), the natural next axis is `universe` denominator expansion — testing whether v1's basin-lock is universe-bound (dilution will reshape it) or regime-bound (ETH catastrophic drag persists across symbol set changes), with SOL as the candidate having lowest BTC correlation (ρ=0.62) and clean dead-feed status per /017 EDA Table 2.

---

## Section 1 — Hypothesis

**Adding SOLUSDT as a single-symbol Model F (preserving baseline A/C/D/E semantics)** in a 6-symbol universe will (a) dilute LINK's denominator-bound 137.66% baseline OOS share via portfolio total expansion, (b) discriminate between regime-bound and universe-bound diagnoses for ETH's 3-axis structural drag (across /014/015/016, all catastrophic OOS), and (c) introduce a new cross-symbol diversification component to the portfolio Sharpe denominator with SOL's 3.68% IS std (highest in universe) and lowest-in-universe BTC correlation.

The intervention is universe expansion ONLY: NO sample-weighting change (`abs_pnl` reverted per /016 finding), NO labeling change (baseline ATR 2.9/1.45 for SOL pooling — same ATR as Model A), NO feature change (V1_FEATURE_COLUMNS_PRUNED unchanged), NO risk-gate change (Model F gets R3 OOD only — sister to Model A).

**Predicted outcome distribution at v1 EXPLORATION (FLAT 33/33/34 per /015 + /016 LM Master rule)**:
- 33% PROMISING (Δ OOS Sharpe ≥ +0.20)
- 33% NULL (|Δ| < 0.20)
- 34% NEGATIVE (Δ ≤ -0.20)

**Mechanism-level predictions (CAUTIOUS — no per-symbol-direction concentrated priors)**:
- F-AXIS-MECHANISM-NEW: SOL trade count > 0 (clean Model F dispatch) AND SOL share of total portfolio absolute PnL ∈ [5%, 40%] (CAUTIOUS band; signals neither dead-feed nor lottery)
- ETH OOS share of portfolio absolute PnL: 3 scenarios pre-registered (Table 3, Section 2)
- LINK concentration: predicted to drop if SOL contribution ≠ 0 (Table 2, Section 2)

---

## Section 2 — IS-Only Evidence (EDA tables)

All numbers from committed scripts under `analysis/iteration_v1-017/`:
- `eda_symbol_data_availability.py` → `data_availability_summary.csv` + `dead_feed_screen.csv` + `pricing_distribution.csv` + `is_correlation_vs_btc.csv`
- `eda_eth_structural_drag.py` → `eth_drag_per_iteration.csv` + `denominator_dilution_prediction.csv` + `regime_vs_universe_hypothesis.csv`
- `eda_concentration_predictions.py` → `concentration_prediction.csv` + `sol_xrp_forward_expectation.csv` + `volatility_profile_comparison.csv` + `architecture_decision.csv`
- `eda_wall_clock_estimate.py` → `wall_clock_scenarios.csv`

### 2.1 Symbol data availability (PASS for SOL + XRP)

**Table A — kline coverage** (`data_availability_summary.csv`):

| Symbol | n_klines | first_open | last_open | covers_training | covers_OOS | days_of_OOS |
|---|---|---|---|---|---|---|
| BTCUSDT | 7002 | 2020-01-01 | 2026-05-22 | YES | YES | 424 |
| ETHUSDT | 7002 | 2020-01-01 | 2026-05-22 | YES | YES | 424 |
| LINKUSDT | 6953 | 2020-01-17 | 2026-05-22 | YES | YES | 424 |
| LTCUSDT | 6962 | 2020-01-09 | 2026-05-22 | YES | YES | 424 |
| DOTUSDT | 6300 | 2020-08-22 | 2026-05-22 | YES | YES | 424 |
| **SOLUSDT** | 6203 | 2020-09-14 | 2026-05-18 | **YES** | **YES** | **420** |
| **XRPUSDT** | 6958 | 2020-01-06 | 2026-05-18 | **YES** | **YES** | **420** |

**Reading**: Training start is 2023-04-04 (OOS_CUTOFF=2025-03-24 minus 24mo); SOL data starts 2020-09-14 (≥ 2yr buffer) and XRP starts 2020-01-06 (≥ 3yr buffer). Both have 420 days of OOS (vs baseline 424; small ~4-day gap with no material impact on OOS Sharpe). **PASS.**

### 2.2 A14 dead-feed pre-screen (PASS for SOL + XRP)

**Table B — dead-feed detector** (`dead_feed_screen.csv`, threshold=50 candles):

| Symbol | max_consec_flat_close | max_consec_flat_ohlc | zero_vol_candles | dead_feed_flag |
|---|---|---|---|---|
| BTCUSDT-DOTUSDT (baseline) | 1 | 0 | 0 | FALSE |
| **SOLUSDT** | **1** | **0** | **0** | **FALSE** |
| **XRPUSDT** | **2** | **0** | **0** | **FALSE** |

**Reading**: No A14 dead-feed pattern. Per /006 closeout MKR lesson, dead-feed defects show as 88/116 OOS trades at frozen 1650.10 price — manifesting as max_consecutive_flat_close ≥ 50. SOL/XRP show 1-2 consecutive flat closes (normal for any liquid market). **PASS.**

### 2.3 ETH structural drag — 3-axis evidence (MANDATORY per Critic /016 Rec #2)

**Table C — ETH IS/OOS PnL trajectory across 3 axes** (`eth_drag_per_iteration.csv`):

| Iteration | Axis | ETH_IS_PnL | ETH_OOS_PnL | Portfolio_OOS | ETH_OOS_share% |
|---|---|---|---|---|---|
| baseline | (baseline) | -13.70 | +2.75 | +24.87 | 11.08% |
| /014 | labeling — σ_t LABEL-only | -99.73 | **-41.18** | +3.31 | -1245% (small denom) |
| /015 | labeling — σ_t symmetric multi-seed | +17.34 | **-23.29** | +29.67 | -78% |
| /016 | sample-weighting — uniform | -46.47 | **-51.46** | -67.98 | +76% (negative-share share) |

**Mean ETH OOS across 3 axes: -38.64%.** Three disjoint mechanism layers (label-distribution-shape twice; sample-weight-magnitude once); all three produce ETH OOS catastrophic.

**Diagnostic** (per /016 LM Master Phase 7.4 §5 + Critic Phase 7.5 §Per-symbol Pattern): the drag is **STRUCTURAL** — regime-conditioned, likely 2025-Q1 → 2026-Q1 ETH-specific weakness — NOT iteration-specific.

### 2.4 Regime-vs-universe pre-registered scenarios (MANDATORY per Critic /016 Rec #2)

**Table D — falsifier scenarios** (`regime_vs_universe_hypothesis.csv`):

| Scenario | Label | ETH share threshold | ETH OOS PnL threshold | Implication |
|---|---|---|---|---|
| A | ETH-still-catastrophic | > 40% of absolute portfolio PnL | ≤ -20% | **Regime-bound**; /018 pivots to ETH-specific kill switch |
| B | Benign-dilution | ≤ 30% of absolute portfolio PnL | ∈ [-15, +5]% | **Universe-bound**; further expansion considered |
| C | ETH-recovery | neutral / positive contributor | ≥ 0% | Model-architecture-driven recovery (per-symbol Model A reset by 6-sym dispatch) |

**Pre-registered: /017 outcome will land in exactly one of A/B/C.** Brief Section 8 verdict matrix pre-registers all three.

### 2.5 Concentration dilution prediction (LINK 137.66% share reduction)

**Table E — LINK share scenarios under SOL contribution** (`concentration_prediction.csv`, excerpt):

| SOL OOS contrib | new portfolio total | LINK share | LINK delta vs baseline |
|---|---|---|---|
| -10% | 14.87 | 230.20% | +92.54pp |
| -5% | 19.87 | 172.27% | +34.61pp |
| 0% | 24.87 | 137.64% | -0.02pp |
| **+5%** | **29.87** | **114.60%** | **-23.06pp** |
| **+10%** | **34.87** | **98.16%** | **-39.50pp** |
| +15% | 39.87 | 85.85% | -51.81pp |

**Reading**: At SOL OOS contribution ≥ +10%, LINK denominator-bound share drops below 100% (i.e., LINK no longer >100% of portfolio total). This is the **denominator-dilution mechanism**. NOT a directional claim about portfolio Sharpe; merely shows the dilution math.

### 2.6 SOL/XRP volatility profile (Table F)

**Table F — SOL/XRP vs LINK/DOT vol stats** (`volatility_profile_comparison.csv`):

| Symbol | role | IS std | IS abs_p95 | IS abs_p99 | IS skew | IS kurtosis |
|---|---|---|---|---|---|---|
| LINKUSDT | baseline | 3.24% | 6.67% | 11.38% | -0.37 | 5.21 |
| DOTUSDT | baseline | 3.12% | 6.49% | 11.66% | -0.17 | 7.61 |
| **SOLUSDT** | **candidate** | **3.68%** | **7.52%** | **12.45%** | +0.25 | 8.41 |
| XRPUSDT | candidate | 3.04% | 5.99% | 11.84% | +0.03 | **17.46** |

**Reading**: SOL fits naturally in the universe vol profile — std slightly above LINK (3.68% vs 3.24%); skew slightly positive vs baseline 3 symbols having slight negative skew (consistent with SOL's stronger uptrends in past cycles). XRP has very high kurtosis (17.46) suggesting fat tails — possible reason for /015 candidate rejection from baseline 5-sym.

### 2.7 IS correlation with BTC — diversification rationale

**Table G — IS log-return correlation vs BTC** (`is_correlation_vs_btc.csv`):

| Symbol | IS corr_vs_BTC |
|---|---|
| BTCUSDT | 1.0000 |
| ETHUSDT | 0.8327 |
| LINKUSDT | 0.6856 |
| LTCUSDT | 0.7510 |
| DOTUSDT | 0.6948 |
| **SOLUSDT** | **0.6164** |
| XRPUSDT | 0.5946 |

**Reading**: SOL ρ=0.6164 is BELOW ANY baseline symbol (lowest baseline = LINK at 0.6856). SOL is the **strongest non-BTC-correlated candidate** per LM Master Phase 7.4 §6 preference. XRP is even lower at 0.5946 but has the high-kurtosis flag. SOL primary, XRP alternate per the LM Master directive.

### 2.8 Universe architecture decision — ISOLATED Model F (single-axis isolation)

**Table H — architecture options** (`architecture_decision.csv`):

| Architecture | Model count | Scale vs baseline | Rationale |
|---|---|---|---|
| Add SOL as ISOLATED Model F | 5 | 1.25× | preserves baseline A/C/D/E semantics |
| Add SOL to POOLED-A | 4 | 1.20× | smaller model count BUT confounds Model A's training distribution |
| Single fully-pooled 6-sym model | 1 | 1.50× | ABANDONS architecture entirely; CONFOUNDS axis (universe + model-arch) |

**CHOSEN: ISOLATED Model F** — preserves baseline A/C/D/E semantics; SOL gets dedicated single-symbol model; 6-model dispatch follows /006 precedent. Single-axis universe expansion test — clean attribution.

### 2.9 SOL/XRP feature parquet — STALE DATA ALERT (BLOCKING)

**Table I — feature parquet diff vs baseline (DATA INFRASTRUCTURE BLOCKER)**:

| Symbol | features_parquet rows | last_open | feature_cols | V1_PRUNED missing cols |
|---|---|---|---|---|
| BTCUSDT (baseline) | 7002 | 2026-05-22 | 215 | 0 |
| **SOLUSDT** (candidate) | **5967** | **2026-02-28** | **196** | **8** |
| **XRPUSDT** (candidate) | **6722** | **2026-02-28** | **196** | **8** |

**SOL/XRP features parquets are STALE** (last open 2026-02-28 vs baseline 2026-05-22 — 83 days of OOS missing) AND **missing 8 of 40 V1_FEATURE_COLUMNS_PRUNED features**:
- `cal_dow_norm`, `cal_hour_norm`
- `interact_natr_x_adx`, `interact_ret1_x_natr`, `interact_ret1_x_ret3`
- `interact_rsi_x_adx`, `interact_rsi_x_natr`, `interact_stoch_x_adx`

**MANDATORY pre-launch step** (Section 10.4):
```bash
uv run crypto-trade features --symbols SOLUSDT --interval 8h --track v1 --format parquet --workers 1
```

This regenerates `data/features/SOLUSDT_8h_features.parquet` with current klines (through 2026-05-18) and all 215 columns.

QE Phase 6 cannot launch the backtest until SOL features are regenerated. Phase 5.5 gate verifies the regen step appears in QE dispatch spec.

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1-only)

- **Declaration**: **HIGH-RISK**
- **Reason**: Universe expansion adds a NEW symbol to training data (Model F is trained on SOL — never seen by baseline models). This changes Optuna's training-objective domain (one new model trained with full per-cell Optuna budget — n_trials × ENSEMBLE_SIZE for SOL's IS window). Per `feedback_v1_n_eff_barrier_magnitude_curve.md` LESSON #2, axes that introduce NEW training data into the v1 substrate are HIGH-RISK.
- **Mitigation (opt-in)**: NONE — single-seed-style EXPLORATION at ENSEMBLE_SIZE=3 inner seeds (fixed cycle-3 default per `feedback_v1_wall_clock_discipline_enforced.md`). The v1 HIGH-RISK rule is OPT-IN multi-seed validation, but ENSEMBLE_SIZE=3 is already fixed by cycle-3 wall-clock discipline. /017 records the choice and the OOS outcome; if /017 + the next 2 HIGH-RISK EXPLORATIONs produce ≥1σ negative OOS deltas, the feedback rule will mandate multi-seed validation per the LESSON #2 forward-mandate.

---

## Section 3 — Proposed Changes

### 3.1 Universe expansion — single axis (SOL only)

NEW universe constant `V1_ITER017_UNIVERSE` defined locally in `run_baseline_v1.py` (NOT in `features_v1/__init__.py` — only CONFIRMATION-MERGE updates the shared constant):

```python
# iter-v1/017 — universe expansion EXPLORATION (cycle-3 #2; PRIMARY)
V1_ITER017_UNIVERSE = (
    "BTCUSDT",
    "ETHUSDT",
    "LINKUSDT",
    "LTCUSDT",
    "DOTUSDT",
    "SOLUSDT",   # NEW — Model F
)
```

NEW elif branch in runner symbol dispatch (after existing baseline branch at lgbm.py:1148):

```python
elif set(symbols) == set(V1_ITER017_UNIVERSE):
    # iter-v1/017: 5-model dispatch with Model F (SOL) added.
    # Models A/C/D/E IDENTICAL to baseline 4-model dispatch (regression-safe).
    results_a, faxm_a = run_model("A (BTC/ETH)", ("BTCUSDT", "ETHUSDT"), atr_tp=2.9, atr_sl=1.45, apply_r1=False, ...)
    results_c, faxm_c = run_model("C (LINK + R1)", ("LINKUSDT",), atr_tp=3.5, atr_sl=1.75, apply_r1=True, ...)
    results_d, faxm_d = run_model("D (LTC + R1)", ("LTCUSDT",), atr_tp=3.5, atr_sl=1.75, apply_r1=True, ...)
    results_e, faxm_e = run_model("E (DOT + R1 + R2)", ("DOTUSDT",), atr_tp=3.5, atr_sl=1.75, apply_r1=True, apply_r2=True, ...)
    # NEW Model F — SOL, single-symbol, R3-only (sister to Model A pooling), atr=2.9/1.45 (Model A profile)
    results_f, faxm_f = run_model("F (SOL)", ("SOLUSDT",), atr_tp=2.9, atr_sl=1.45, apply_r1=False, ...)
    _all_faxm_logs = faxm_a + faxm_c + faxm_d + faxm_e + faxm_f
    all_results = results_a + results_c + results_d + results_e + results_f
    _r5_model_results = [results_a, results_c, results_d, results_e, results_f]
```

### 3.2 No other axis changes (single-axis isolation)

- Sample-weighting: REVERT to `abs_pnl` (per /016 finding — `uniform` and `uniqueness_only` are CLOSED for v1; baseline mode preserved). Brief explicitly sets `--sample-weight-mode abs_pnl` (CLI default).
- Labeling: ATR×2.9 TP / ATR×1.5 SL / 21-candle timeout (baseline default; SOL Model F uses Model A's atr profile because SOL profile is closest to BTC+ETH pooled, not LINK/LTC/DOT single-symbol). `--label-sigma-source natr` explicit.
- Features: V1_FEATURE_COLUMNS_PRUNED unchanged (40 cols).
- Candles: 8h (baseline interval; per skill, cannot change without re-anchoring baseline).
- Risk gates: R1 (C/D/E only), R2 (E only), R3 (ALL — including new F), UNCHANGED. Model F gets R3 OOD ONLY (sister to Model A).
- OOD features: V1_OOD_FEATURE_COLUMNS UNCHANGED.
- Bounds profile: `v1_pruned` (UNCHANGED). NO `v1_pruned_per_symbol_expansion` profile (that was /006's bounds for FIL/MKR with TIGHTER colsample 0.5→0.7 and HIGHER min_child_samples 20→30; that was justified by /006's hypothesis-specific reasoning; /017 keeps Model F at the same `v1_pruned` profile as Models A/C/D/E for cleanest single-axis isolation).
- ENSEMBLE_SIZE: 3 inner seeds (fixed cycle-3 default; canonical `[42, 123, 456]`).
- Optuna: `--n-trials 18` (compressed from default 35 per wall-clock discipline; was /016's value; > TPE warmup ~10).

### 3.3 LM Master Phase 4.5 response slot

(LM Master is invoked at Phase 4.5 PRIOR to brief authoring; Phase 4.5 recommendations land in `briefs-v1/iteration_v1-017/lgbm_advisor.md`. As of brief authoring, the LM Master Phase 4.5 file is **PENDING** and will be appended by orchestrator before Phase 5.5 gate. Brief Section 3.4 receives an "Adopted/Modified/Rejected per recommendation" reply for each LM Master rec.)

### 3.4 (Reserved) Response to LM Master Phase 4.5 recommendations

To be authored after `briefs-v1/iteration_v1-017/lgbm_advisor.md` Phase 4.5 section is committed by orchestrator. Brief Section 3.4 will contain explicit "Adopted" / "Modified" / "Rejected" responses to each of LM Master's 2-4 hyperparameter recommendations + 1-2 feature-engineering ideas + saturation risks + confidence assessment, per v1-Specific Disciplines §1.

### 3.5 (Sub-section continues for any axis-spec amendments after LM Master)

Reserved for amendments. Default: brief Section 3.1-3.2 as authored.

### 3.6 Wall-clock estimate (CRITICAL — Phase 5.5 BLOCK if missing or > 1.6h estimate / < 20% margin)

#### 3.6.1 /016 empirical anchor

Per `reports-v1/iteration_v1-016/engineering_report.md` §6.1:
- 5-sym universe (BTC+ETH+LINK+LTC+DOT) — 4 models A/C/D/E
- ENSEMBLE_SIZE=3, n_trials=18, V1_FEATURE_COLUMNS_PRUNED (40 cols), 8h candles
- Observed: **~50 minutes** total wall-clock
- /016 LESSON #5: prediction band 1.50-1.75h was 2-3× OVER-CONSERVATIVE; sub-linear correction = 0.7×

#### 3.6.2 /017 6-sym linear scaling estimate

From /016's 50-min anchor:
- Symbol factor: 6/5 = 1.20× (new Model F = +1 single-symbol model run, ~ Model C/D/E magnitude)
- n_trials: 18/18 = 1.0× (unchanged)
- ENSEMBLE_SIZE: 3/3 = 1.0× (unchanged)
- Features: 40/40 = 1.0× (unchanged)

Linear estimate: 50 × 1.20 = **60 min** (1.00 hour)

#### 3.6.3 Decision and margin

- **Predicted wall-clock**: 60 min (linear) OR 42 min (sub-linear realistic estimate per /016 LESSON #5)
- **Cap**: 2h EXPLORATION
- **Margin (linear)**: (120 - 60) / 120 = **50%** ≥ 20% ✓
- **Margin (sub-linear)**: (120 - 42) / 120 = **65%** ≥ 20% ✓

Both estimates comfortably exceed the 20% Phase 5.5 floor. NO compression needed.

#### 3.6.4 Compression decision rationale

NO compression applied. The 6-sym universe (1 new model) is well within the 2h cap at /016's empirical anchor.

If QE pre-flight indicates wall-clock overshoot relative to estimate (>72 min at 50% completion), compress n_trials 18→15 per skill precedence rule #1 (Optuna saturation tolerance). Stays above TPE warmup ~10.

#### 3.6.5 Trade-off rationale

- **Sacrificed**: nothing (no compression).
- **Gained**: clean single-axis universe expansion test with /016-anchored wall-clock; clean baseline-architecture preservation (Models A/C/D/E IDENTICAL to baseline).
- **Forward**: if /017 PROMISING, /027 CONFIRMATION at ENSEMBLE_SIZE=10 × 6 models ≈ 50 × (10/3) × (6/5) = ~200 min = 3.3h (well within 6h CONFIRMATION cap).

---

## Section 4 — Falsifiers (F1-F8 + F-AXIS-MECHANISM)

### F1 — multi-seed mean OOS Sharpe Δ vs baseline (informational at EXPLORATION)

- Falsifier band: Δ ∈ [-0.30, +0.30] (FLAT prior at single-seed EXPLORATION per /015/016 LM Master rule)
- PROMISING-INFORMATIONAL threshold: Δ ≥ +0.20 (signals PATH B for /018+)
- NEGATIVE threshold: Δ ≤ -0.20
- Catastrophic floor: Δ ≤ -0.55

### F2 — feature-rank Spearman ρ across symbols: STRUCTURAL-locked per /005

Not retested. Prior structural finding holds (Spearman ρ across radically different axis interventions stays ~0.95 at single-seed; F2 is DEMOTED to STRUCTURAL-only per /005 closeout AXIOM).

### F3 — IS Sharpe Δ vs baseline

- Falsifier band: Δ ∈ [-0.20, +0.20] (FLAT prior)
- Catastrophic: Δ < -0.30

### F4 — Top-symbol OOS concentration

- Falsifier: top-symbol_pnl_share ≤ 50% of total ABSOLUTE OOS portfolio PnL (informational at EXPLORATION; merge gate is 30%)

### F5 — Win-rate stability

- Falsifier: 35% ≤ WR ≤ 50% (within baseline range; portfolio WR baseline 40.2%)

### F6 — Max drawdown

- Falsifier: OOS MaxDD ≤ 60% (within baseline 40.94% × 1.5)

### F7-NEW — Per-symbol direction consistency

- Falsifier: PASS = 6/6 per-symbol IS Δ same-sign as portfolio IS Δ; PARTIAL = 4-5/6; FAIL = ≤3/6

### F8-NEW — Trade-count band (post-expansion)

- /017 expanded trade-count baseline: baseline 621 IS × (6/5) = 745; falsifier band: 559 ≤ IS_trades ≤ 931 (621 × [0.9, 1.5] reflecting symbol-add scaling)
- OOS trade-count band: baseline 189 OOS × (6/5) = 227; falsifier band: 170 ≤ OOS_trades ≤ 284

### F-AXIS-MECHANISM-NEW (NEW; universe expansion axis attribution)

**Compound falsifier — ALL THREE sub-checks must PASS for axis attribution confirmation**:

1. **Model F dispatch fires**: F-row count in run_model logs = 1 (one new model added); SOL appears as a discrete model_name in the reports; SOL OOS trade count > 0.

2. **SOL share of total ABSOLUTE OOS portfolio PnL ∈ [5%, 40%]**: lower bound (5%) ensures Model F isn't an A14-style dead-feed degenerate (zero/near-zero contribution); upper bound (40%) ensures SOL doesn't dominate portfolio in single-seed lottery (concentration violation triggering F4).

3. **n_eff_per_cell substrate** (per /016 NEW mandate — `feedback_v1_abs_pnl_weighting_structural.md` Mandate #2): n_eff_per_cell_median across all (model, month) cells ∈ [10, 18] (preserves the /016 baseline-labels regime; universe expansion shouldn't materially shift the label-shape n_eff substrate).

**Forward mandate for "uniform-anything" sub-check applicability**: /017 does NOT uniformize anything; it adds a symbol. Per /016 NEW mandate, n_eff_per_cell is the **independent edge-attribution sub-check**. The 3 sub-checks above are NOT identity-redundant (1 is dispatch-check, 2 is SOL-specific contribution check, 3 is substrate-check).

**Expected PASS by construction**: only sub-check #1 (Model F dispatch fires) is mechanism-deterministic; #2 and #3 are genuinely informative (SOL contribution could be near-zero if Model F fails to find a signal; n_eff could shift if SOL's IS regime is materially different from baseline's 5-sym regime). UNLIKE /016, F-AXIS-MECHANISM is NOT a WIRING-test-only — it has real edge-attribution content.

### F-AXIS-MECHANISM PASS by construction guard (per /016 LESSON #2)

Per `feedback_v1_abs_pnl_weighting_structural.md` Mandate #2: future "uniform-anything" / "identity-anything" axes must include an independent edge-attribution sub-check. /017 is NOT a uniformization axis (no constant-collapse of any vector); this guard is NOT applicable to /017's F-AXIS-MECHANISM. Sub-check #3 (n_eff_per_cell) is included anyway as DURABLE evidence per /016 finding.

---

## Section 5 — Predicted Outcomes

| Verdict-class | Probability | Mechanism description |
|---|---|---|
| PROMISING (Δ ≥ +0.20) | 33% | If SOL contributes positively AND ETH benefits from denominator dilution AND no model-arch confound, portfolio OOS Sharpe could lift to 0.85+ range. |
| NULL (\|Δ\| < 0.20) | 33% | If SOL contributes near-zero OOS (new-symbol regime mismatch with baseline 5-sym) AND ETH drag persists, portfolio OOS Sharpe stays in 0.50-0.85 band. |
| NEGATIVE (Δ ≤ -0.20) | 34% | If SOL contributes negative OOS (single-seed lottery; new-symbol overfit) OR ETH catastrophic plus LINK denominator-dilution drops LINK share too sharply, portfolio OOS Sharpe collapses. Cycle-2 cycle-3 priors empirically show v1 basin punishes most interventions. |

**Total**: 100%. **Expected E[F1 OOS Δ]** ≈ +0.20×0.33 + 0.0×0.33 + (-0.20)×0.34 = -0.001 (essentially zero) ← reflects FLAT priors honestly per /015 + /016 + LM Master Phase 4.5 §1 rule.

**Mechanism-level prediction** (HIGHER confidence):
- F-AXIS-MECHANISM-NEW sub-check #1 (Model F dispatch) PASS at >99% (code-correctness check; QE Phase 6.0 verifies)
- F-AXIS-MECHANISM-NEW sub-check #2 (SOL share ∈ [5%, 40%]) PASS at MEDIUM ~70% — but legitimate failure can be NEGATIVE-no-contribution (SOL share < 5%) OR concentration-violation (SOL share > 40%)
- F-AXIS-MECHANISM-NEW sub-check #3 (n_eff ∈ [10, 18]) PASS at MEDIUM ~75% — baseline-labels regime expected to preserve this band, but a 6-sym universe adds rows to the OOF parquet via Model F → PCA on a larger trial-return matrix could shift n_eff slightly

---

## Section 6 — Failure Modes (pre-registered)

### 6.1 Failure mode A: NULL-RESULT (most likely)

- F1 OOS Δ ∈ [-0.20, +0.20]; F-AXIS-MECHANISM PASS (Model F fires; SOL share ∈ [5%, 40%]; n_eff in band)
- Interpretation: universe expansion mechanically fired (Model F trained, SOL contributed), but no edge gained or lost on portfolio Sharpe
- Catalog row: `EXPLORATION-NULL` (universe expansion axis CLOSED at +1 symbol; /018 = different family OR ETH-specific kill switch)
- Forward axis: /018 = different family (e.g., model-arch XGBoost OR ETH-conditional kill per Critic /016 Path Forward #3)

### 6.2 Failure mode B: NEGATIVE-NEGATIVE compound

- F1 OOS Δ ≤ -0.20 AND F3 IS Δ ≤ -0.20
- Interpretation: universe expansion hurt both halves
- Catalog row: `EXPLORATION-NEGATIVE` (subtype assigned by Critic — could be `BASIN-LOTTERY-CATASTROPHIC` if F-AXIS-MECHANISM PASS-clean OR `NEGATIVE-CONTAMINATION` if SOL share is the catastrophic driver)
- Forward axis: /018 = ETH-specific kill switch OR per-symbol drawdown brake (per Critic /016 Path Forward #3)

### 6.3 Failure mode C: PROMISING with F-AXIS-MECHANISM FAIL

- F1 OOS Δ ≥ +0.20 BUT F-AXIS-MECHANISM-NEW FAIL (Model F not firing OR SOL share outside [5%, 40%])
- Interpretation: code defect — perhaps the universe-expansion elif branch dispatched but symbols weren't passed through correctly
- Catalog row: PROMISING with critical mechanism-FAIL flag; BLOCK-PENDING-FIX

### 6.4 Failure mode D: PROMISING with F-AXIS-MECHANISM PASS

- F1 OOS Δ ≥ +0.20 AND F-AXIS-MECHANISM PASS
- Interpretation: universe expansion lifted OOS Sharpe; either (a) SOL contributed positively (universe-bound dilution mechanism worked) OR (b) Model F training shifted Optuna's loss surface improving baseline cells
- Catalog row: `EXPLORATION-PROMISING` (subtype TBD by Critic — could be PROMISING-MECHANICAL if trade-roster bit-identical for A/C/D/E and SOL drove all the lift)
- Forward axis: /018+ accumulate EXPLORATIONs toward /026 CONFIRMATION (pre-committed cycle-3 cadence per /016 Critic Path Forward)

### 6.5 Failure mode E: PROMISING-MECHANICAL

- F1 OOS Δ ≥ +0.20 BUT trade-roster bit-identical for A/C/D/E vs baseline AND SOL drove all the lift via dilution mechanism (not signal-discovery)
- Catalog row: `EXPLORATION-PROMISING-MECHANICAL` (sister to v3 PROMISING-MECHANICAL precedent; non-compoundable as signal source)
- Forward axis: NOT bundled at /027 CONFIRMATION — would require validation as separate ingredient

### 6.6 Failure mode F: A14 dead-feed on SOL (pre-flight should catch)

- F-AXIS-MECHANISM-NEW sub-check #2 FAIL (SOL share < 5%); Model F shows mass of trades at frozen price
- Pre-flight EDA Table B says SOL is CLEAN; this would mean post-EDA data corruption (e.g., feature regen produces NaN/inf)
- Catalog row: BLOCK-PENDING-FIX (data integrity); /017 rerun after fix

### 6.7 Failure mode G: regime-bound ETH STRUCTURAL drag

- F1 OOS Δ ∈ any band AND ETH OOS PnL ≤ -20% (Scenario A from §2.4)
- Interpretation: ETH drag is regime-bound (NOT universe-bound); 4th consecutive axis-disjoint catastrophic ETH OOS
- Catalog row: verdict-class per F1; ADDITIONAL forward-binding mandate: /018 PRIMARY = ETH-specific kill switch (per Critic /016 Path Forward #3)

---

## Section 7 — BASELINE_V1 Update Conditions

EXPLORATION never updates BASELINE_V1. /017 is EXPLORATION (cycle-3 #2; 10:1 cadence requires 10 EXPLORATIONs before /027 CONFIRMATION).

If /017 is PROMISING and survives F-AXIS-MECHANISM PASS, the +SOL universe expansion becomes a candidate for /027 CONFIRMATION bundling. The decision to bundle is the future CONFIRMATION-QR's call, not /017's. Bundling considerations would include: does SOL's contribution stack with other cycle-3 ingredients (none yet — /016 closed); does the 6-sym universe survive multi-seed validation; is the dilution mechanism repeatable across seeds.

---

## Section 8 — Verdict Gates (Cell Matrix, 5-class per Critic /010 Rec #1)

| Cell | F1 OOS Δ | F3 IS Δ | F7-NEW | F8-NEW | F-AXIS-MECHANISM | Verdict |
|---|---|---|---|---|---|---|
| 1 | ≥ +0.20 | ≥ +0.10 | PASS or PARTIAL (≥4/6) | PASS | PASS (all 3 sub-checks) | **EXPLORATION-PROMISING** |
| 2 | ≥ +0.20 | < +0.10 | PASS or PARTIAL | PASS | PASS | **EXPLORATION-PROMISING-MECHANICAL** (or NULL if trade-roster A/C/D/E bit-identical) |
| 3 | ∈ [-0.20, +0.20] | any | PASS or PARTIAL | PASS | PASS | **EXPLORATION-NULL** |
| 4 | ∈ [-0.20, +0.20] | any | any | PASS | FAIL (any sub-check) | **EXPLORATION-NULL-FLAGGED** (mechanism FAIL = src/ defect — BLOCK-PENDING-FIX) |
| 5 | ≤ -0.20 | any | PASS or PARTIAL | PASS | PASS | **EXPLORATION-NEGATIVE** |
| 6 | ≤ -0.55 | ≤ -0.30 | any | PASS | PASS | **EXPLORATION-NEGATIVE-catastrophic** |
| 7 | any | any | FAIL (≤3/6) | PASS | any | **EXPLORATION-NEGATIVE-mechanism** |
| 8 | any | any | any | FAIL | any | **EXPLORATION-NEGATIVE-mechanical** (trade-count band breach) |
| 9 | any | any | any | any | sub-check #2 FAIL (SOL < 5% OR > 40%) | **EXPLORATION-NULL-FLAGGED-SYM-CONTRIB** (SOL-specific dispatch/contribution anomaly) |

**Cells 8/9 mechanical failures CHECKED FIRST per /014 brief Section 8.2 override rule.**

---

## Section 9 — Library Stack

Mandatory imports — all already present in production:
- `numpy` (array operations)
- `pandas` (master DataFrame; per-symbol grouping)
- `lightgbm` (gradient boosting; sample_weight unchanged — abs_pnl default)
- `optuna` (TPE sampler; trial returns persistence)

NO new third-party dependencies. Implementation is:
1. NEW universe constant `V1_ITER017_UNIVERSE` in `run_baseline_v1.py` (LOCAL — not shared)
2. NEW elif branch in symbol dispatch (after baseline branch at lgbm.py:1148)
3. Mandatory pre-launch step: `crypto-trade features --symbols SOLUSDT --interval 8h --track v1 --format parquet`

---

## Section 10 — Implementation Spec (QE)

### 10.1 Files to modify

1. **`run_baseline_v1.py`**:
   - Add `V1_ITER017_UNIVERSE` constant (LOCAL, 6 symbols; BTC+ETH+LINK+LTC+DOT+SOL)
   - Add `elif set(symbols) == set(V1_ITER017_UNIVERSE):` 5-model dispatch
     - Models A/C/D/E IDENTICAL to baseline 4-model dispatch (BIT-IDENTICAL for regression-safe)
     - NEW Model F (SOL): atr_tp=2.9, atr_sl=1.45, apply_r1=False, R3 OOD only, bounds_profile='v1_pruned' (SAME as A/C/D/E)
   - Update aggregation loops to include results_f + faxm_f + _r5_model_results
   - The runner's existing fallback (single POOLED model for non-recognized universes) stays for future universe-axis iterations to be safe.

2. **No `src/` changes required**:
   - `features_v1/__init__.py` unchanged (V1_BASELINE_UNIVERSE stays the same; V1_EXCLUDED_SYMBOLS unchanged — universe expansion is RUNNER-local for EXPLORATION)
   - `lgbm.py` unchanged (sample_weight_mode=abs_pnl default; F's Optuna training reuses existing infrastructure)
   - `walk_forward.py` unchanged (the foundation discipline is preserved)

### 10.2 MANDATORY PRE-LAUNCH STEP — feature regeneration for SOL

```bash
# Regenerate SOL features through current kline extent (2026-05-18)
# with all V1 215 feature columns including the 8 currently-missing ones.
uv run crypto-trade features \
  --symbols SOLUSDT \
  --interval 8h \
  --track v1 \
  --format parquet \
  --workers 1
```

QE Phase 6 dispatch MUST verify (before backtest launch) that `data/features/SOLUSDT_8h_features.parquet`:
- Has last_open ≥ 2025-04-24 (1 month past OOS_CUTOFF; baseline is 2026-05-22)
- Has all 40 V1_FEATURE_COLUMNS_PRUNED columns

If verification fails, QE STOPS and reports to orchestrator (Phase 5.5 gate verified the regen step exists in dispatch spec).

### 10.3 Engineering report (BLOCKING per /015 LESSON closure)

`reports-v1/iteration_v1-017/engineering_report.md` MUST exist before Phase 7.5 dispatch can fire. Per /015 §LESSON closing fix + /016 Critic Rec #1 (5th-strike): **NO `--no-engineering-report` flag use** at /017. Orchestrator dispatch invocation MUST NOT contain that flag.

### 10.4 Tests to add

1. **Unit test**: `tests/test_iteration_v1_017_universe_expansion.py` — verifies:
   - `V1_ITER017_UNIVERSE` constant exists and contains exactly (BTCUSDT, ETHUSDT, LINKUSDT, LTCUSDT, DOTUSDT, SOLUSDT)
   - The elif branch is taken when `--symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT,SOLUSDT` is passed (regression-safe vs baseline)
   - The baseline 4-model dispatch produces BIT-IDENTICAL Models A/C/D/E results when `--symbols` is omitted (auto-uses V1_BASELINE_UNIVERSE)

2. **Integration smoke test**: `tests/test_run_baseline_v1_iter017_smoke.py` — runs the runner for 1 IS month × 6 symbols × n_trials=3 × ENSEMBLE_SIZE=1 and verifies:
   - 5 models dispatched (A, C, D, E, F)
   - SOL appears in trades.csv with at least 1 trade
   - comparison.csv has expected rows
   - F-axis logs contain Model F entry

### 10.5 Runner invocation (deterministic)

```bash
uv run python run_baseline_v1.py \
  --exploration --iteration 17 \
  --symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT,SOLUSDT \
  --n-trials 18 \
  --pruned-features \
  --sample-weight-mode abs_pnl \
  --label-sigma-source natr
```

Explicitly:
- `--sample-weight-mode abs_pnl` — REVERT to baseline weighting (NO uniform / NO uniqueness_only); /016 finding makes this the load-bearing setting
- `--label-sigma-source natr` — preserve baseline ATR labeling (NO σ_t-EWMA labels per /014/015 NEGATIVE)
- `--pruned-features` — V1_FEATURE_COLUMNS_PRUNED (40 cols) — same as /016 baseline
- `--n-trials 18` — cycle-3 default; same as /016
- `--exploration --iteration 17` — sets ENSEMBLE_SIZE=3 default + report dir `reports-v1/iteration_v1-017/`
- NO `--no-engineering-report` flag (per /016 5th-strike Critic Rec #1; engineering_report.md is MANDATORY)

### 10.6 Expected wall-clock per QE

- /016 5-sym reference: 50 min observed
- /017 6-sym estimate: 60 min (linear scaling)
- QE KILLs at: 72 min (2h cap × 0.6 tolerance, well-conservative — original cap × 1.2 is 144 min but skill recommends QE stop at predicted-upper × tolerance to leave room for retry)

If wall-clock exceeds 60 min at the 50% completion mark (i.e., projected > 72 min), QE consults orchestrator before continuing. Backup plan: drop n_trials to 15 (still > TPE warmup) — saves ~17%.

---

## Section 11 — Alternates for /018+ (conditional on /017 outcome)

### 11.1 If /017 PROMISING (clean): /018 = continue UNUSED-family rotation

- /017 confirms universe expansion has accessible edge; continue EXPLORATION cadence toward /027 CONFIRMATION
- /018 = XGBoost head-to-head on /017's 6-sym universe (`model-arch` family UNUSED per /016 Path Forward #2 — but DEFER until wall-clock smoke test characterizes XGBoost per /016 Phase 7.4)
- Hold /017's edge candidate for /027 CONFIRMATION bundle

### 11.2 If /017 NULL: /018 = +XRP expansion OR model-arch

- /018 alternate A: add XRP to 7-sym universe (LM Master ALTERNATE per Phase 7.4 — XRP has 0.59 BTC corr lowest; high kurtosis 17.46 caveat)
- /018 alternate B: XGBoost model-arch test (UNUSED family per /016 Critic Path Forward #2)

### 11.3 If /017 NEGATIVE: /018 = ETH-specific kill switch (per /016 Critic Path Forward #3)

- ETH OOS catastrophic across /014/015/016/017 → 4-axis structural confirmation
- /018 = regime-conditional ETH-exclusion gate (NOT proportional cap; NOT static threshold — those v3 deadlock patterns)
- Mechanism options: BTC-trend ETH-conditional gate; ETH-specific ATR-bandwidth filter; per-symbol drawdown brake

### 11.4 If /017 NEGATIVE-mechanism (F-AXIS-MECHANISM FAIL): /018 = BLOCK-PENDING-FIX rerun

- One QE chance to repair the src/ wiring (5-model dispatch elif branch); if F-AXIS-MECHANISM still FAILs after rerun, /018 = different family per Path Forward

---

## Section 12 — Catalog Closeout Plan

Phase 8 diary at `diary-v1/iteration_v1-017.md` will:

1. Record verdict cell from Section 8 (deterministic from F1/F3/F7/F8/F-AXIS values)
2. Update `briefs-v1/exploration_catalog.md` cycle-3 row: family=`universe`, verdict, OOS Sharpe, brief commit SHA
3. If PROMISING: note as edge-ingredient candidate for /027 CONFIRMATION; add to cycle-3 bundle slot
4. If NEGATIVE: append to cycle-3 dead-paths catalog (universe expansion to +SOL at v1 baseline-architecture CLOSED OR DEFERRED — depending on regime/universe diagnostic)
5. If NULL: axis closed at +SOL alone; /018 alternates per §11
6. Record regime-vs-universe diagnostic per Table D scenario landed
7. ETH OOS share landing scenario (A/B/C from §2.4)
8. LINK share dilution landing (Δpp vs baseline 137.66%)
9. Tag commit as `v0.v1-017`

---

## Section 13 — Phase 5.5 Self-Check

### Mandatory presence checks

- [x] Brief Section 0.6 declares axis family `universe` with rotation status VALID (prior 5: 2 methodology-substrate-test, 2 labeling, 1 sample-weighting; `universe` UNUSED since /006)
- [x] Brief Section 1 hypothesis (one-sentence + FLAT prior + mechanism notes)
- [x] Brief Section 2 IS-only EDA tables with committed analysis script paths (4 scripts, 11 CSV outputs)
- [x] Brief Section 2.5 HIGH-RISK declaration with reason (universe expansion adds new training data → HIGH-RISK)
- [x] Brief Section 3.6 explicit wall-clock estimate ≤ 2h cap with ≥20% margin (60 min, 50% margin)
- [x] Brief Section 3.6 compression decision (NONE — no compression needed)
- [x] Brief Section 4 F1-F8 + F-AXIS-MECHANISM-NEW falsifiers (3 sub-checks for universe expansion)
- [x] Brief Section 5 predicted outcomes (FLAT 33/33/34)
- [x] Brief Section 6 failure modes (7 modes: A-G)
- [x] Brief Section 7 BASELINE_V1 update conditions (EXPLORATION never updates)
- [x] Brief Section 8 verdict cell matrix (9 cells)
- [x] Brief Section 9 library stack
- [x] Brief Section 10 implementation spec (QE) — INCLUDING mandatory feature regeneration step + NO `--no-engineering-report`
- [x] Brief Section 11 alternates for /018+
- [x] Brief Section 12 catalog closeout plan
- [x] Brief Section 13 self-check (this section)

### LM Master Phase 4.5 response slot

Section 3.4 reserved for explicit LM Master response. As of brief authoring, LM Master Phase 4.5 advisory is PENDING — orchestrator must invoke `lightgbm-master` Phase 4.5 BEFORE Phase 5.5 gate runs. Brief Section 3.4 receives an "Adopted/Modified/Rejected per recommendation" reply for each LM Master rec.

### Wall-clock margin

- Predicted (linear): 60 min
- Predicted (sub-linear realistic): 42 min
- Cap: 120 min (2h)
- Margin (linear): **50%** (well above 20% Phase 5.5 floor)
- Margin (sub-linear): **65%**
- Compression dimension declared: NONE (no compression needed)
- Trade-off rationale stated: §3.6.5
- Falls within ≥20% margin requirement: YES (both linear and sub-linear)

### Axis Rotation Validity

- Family: `universe` (UNUSED in cycle-3; UNUSED since /006 cycle-2 entry)
- Prior 5: methodology-substrate-test ×2, labeling ×1 (CONFIRMATION ×1), sample-weighting ×1
- Rotation: VALID — `universe` is in NONE of the prior 5 families

### Anti-pattern check

- A1 (look-ahead): NO — no labeling change; no feature recomputation; just adds a symbol
- A2 (survivorship): NO — SOL has full history from 2020-09-14 (>4yr before training start)
- A3 (Sharpe < 50 trades): Need to verify post-run; expected OOS trades ~227 (well above 130 floor)
- A8 (univariate Spearman on features): NO — no feature change
- A12 (axis cherry-pick): NO — only universe axis varies; abs_pnl reverted (NOT a second axis); ATR labels unchanged
- A13 (post-hoc rationalization): NO — falsifiers pre-registered; regime-vs-universe scenarios pre-registered
- A14 (dead-feed): NO — SOL pre-screened CLEAN (max_consecutive_flat_close = 1; zero_volume_candles = 0)

### Critic /016 mandatory acknowledgments

- [x] Critic Rec #2 (ETH OOS catastrophic structural across /014/015/016): explicitly acknowledged in Section 2.3 with full trajectory table; pre-registered regime-vs-universe falsifier in Section 2.4 (3 scenarios A/B/C)
- [x] Critic Rec #1 (5th-strike engineering report opt-out): Section 10.3 explicitly states "NO `--no-engineering-report` flag use at /017"; Section 10.5 runner invocation does NOT include the flag
- [x] Critic Rec #3 (n_eff_per_cell has TWO drivers — label-shape AND weight-distribution): Section 4 F-AXIS-MECHANISM sub-check #3 pre-registers n_eff_per_cell band [10, 18]; universe expansion does NOT touch either driver (no label change, no weight change), so n_eff is expected stable at baseline /016-level

### Brief commit plan

1. Commit #1 (DONE at `2d80ae6`): `feat(iter-v1/017): EDA — symbol data verification + cross-symbol predictions + ETH drag analysis`
2. Commit #2 (PENDING): `docs(iter-v1/017): QR Phases 1-5 + universe expansion brief (cycle-3 #2)`

---

**Phase 5 closeout (QR self-attest)**: brief is complete, mechanisms are pre-registered, wall-clock is bounded (50% margin), axis is clean (single-axis universe expansion ONLY), Critic /016 mandatory acknowledgments are addressed (ETH 3-axis drag in Section 2.3-2.4; engineering report in Section 10.3-10.5; n_eff TWO-driver model in Section 4). Awaiting LM Master Phase 4.5 (orchestrator dispatch) then Phase 5.5 gate.
