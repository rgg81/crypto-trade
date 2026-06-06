# iter-v1/076 — Research Brief

**Iteration**: iter-v1/076
**Date**: 2026-06-06
**TYPE**: SPECIALIST EXPLORATION — **NEW SYMBOL universe-extension** (second under autopilot mining directive 2026-06-06; first DeFi-lending narrative candidate)
**Cycle**: 7, SPECIALIST-MINE 2/N
**Branch**: `iteration-v1/076`
**Author**: QR (autopilot)
**Anchor**: NONE (universe-extension; no prior AAVE specialist exists). Verdict is measured against the implicit dispatch baseline — a single-coin cohort `(AAVEUSDT,)` under the locked SPECIALIST methodology — and ranked **relative to the BUNDLE-001 member IS Sharpe distribution** (DOT/063 IS +0.43, ETH/064 IS +0.24, BTC/065 IS −0.18; mean +0.16, std ≈ 0.30).
**Axis**: **NEW SYMBOL — AAVEUSDT.** Single-bit change vs /063 dispatch: `SYMBOLS=("AAVEUSDT",)` + `ITERATION_LABEL="v1-076"` + ATR pair shifted /063's (3.5, 1.75) → /064's (2.9, 1.45) cell (Model A wrapper match — same as ETH/064 + BTC/065 + ATOM/075). All other methodology constants HELD per user directive 2026-06-06.
**LM Master verdict**: MEDIUM-LOW confidence; modal IS Sharpe **+0.20** (90% band [−0.20, +0.55]); aggregate PROMISING-or-better probability 0.39.

---

## Section 0 — Data Split Declaration (Foundation)

- **OOS_CUTOFF_DATE**: `2025-03-24` (IMMUTABLE — never changes)
- **training_months**: `24` (IMMUTABLE — never changes)
- **IS window**: 2023-03-24 → 2025-03-24 (24 months walk-forward training; AAVE IS roster covers 2160 8h candles, identical row count to all v1 native cohorts)
- **OOS window**: 2025-03-24 → present (1318 8h candles ≈ 14.6 months)
- **Walk-forward embargo**: `train_end_ms = test_start_ms - embargo_ms` (commit `5566a69`; identical helper used in this iteration; inherited bit-exactly from /063 → /064 → /065 → /075 setup)
- **Sacred constants HELD per Rule 3** (`feedback_training_window.md`, `feedback_no_cheating.md`): no shift, no extension, no trim, no peek.

EDA script `analysis/v1-076/eda.py` reads ONLY IS-window klines via the `is_only(df)` helper (filters `open_time < OOS_CUTOFF_MS = 1742774400000`) and asserts `out_of_sample` substring absent from every loaded path (`_assert_is_only_path`). No OOS file is opened during Phase 1-5. The script's `table_09_feature_nan_audit` is the SOLE function that reads OOS-window NaN counts from the same global features parquet (it does not open an OOS-specific file; the parquet has both IS and OOS rows merged). The OOS NaN counts are surfaced as a Phase 5.5 sanity check ONLY — no OOS values are used to derive any signal, threshold, or band edge.

---

## Section 0.5 — Iteration Type Declaration & Cadence

- **TYPE**: SPECIALIST EXPLORATION — NEW SYMBOL (single-coin cohort)
- **Cycle 7 position**: SPECIALIST-MINE 2/N (second universe-extension after BUNDLE-001 merge and after /075 ATOMUSDT)
- **Mining context**: the user directive 2026-06-06 (autopilot — "find new specialists … using all the quantitative knowledge") opened the universe-extension EXPLORATION mode after BUNDLE-001 (v0.v1-071) merged DOT/063 + ETH/064 + BTC/065. All 5 v1-native symbols (BTC, ETH, LINK, LTC, DOT) have been specialist-tested; LINK/066 and LTC/067 ELIMINATED (positive-baseline trap). AAVEUSDT promoted past higher-composite ICP/FTM/EGLD candidates (composite scores 0.27-0.31) on the **NEGATIVE-baseline gate** — AAVE is the ONLY eligible NEW SYMBOL with a NEGATIVE TS-mom IS Sharpe (mine-phase formula cited −0.311; this brief's mom_5/fwd_3 replication gives −0.124 — same SIGN, weaker magnitude). NEGATIVE-pooled-baseline is the necessary precondition for specialist edge extraction per the DOT/063 precedent.
- **Wall-clock budget**: **2h hard cap** per `feedback_v1_confirmation_walltime_9h.md` EXPLORATION default. LM Master Phase 4.5 predicts ~50-90 min Optuna + 10 min wrap-up (50 inner seeds × 30 trials × 24 walk-forward cells; AAVE 5.64y data extent supports stable cell counts).
- **Kill-switch**: if wall-clock exceeds 2.5h, OR any specialist outer-seed returns `nan` Sharpe, OR the FEATURES_BASE_HASH_48COL pre-flight guard fails to match /063's 48-col hash, OR `df[V1_FEATURE_COLUMNS_PRUNED].dropna(subset=non-cross-symbol).shape[0] < 5000` (catastrophic feature coverage break) → abort, capture commit, surface diagnostic for next mining candidate.

---

## Section 0.6 — Architecture-Family Justification (v1)

- **Axis family**: `universe` (NEW SYMBOL — universe-extension to a not-yet-tested coin under LOCKED methodology)
- **Prior 5 EXPLORATION families** (catalog rows /067 → /075):
  - iter-v1/067: `universe` (LTC SPECIALIST EXPLORATION) → ELIMINATED (positive-baseline trap)
  - iter-v1/072: `risk-primitive` (BTC-IMPROVED-V2 R1 streak-cooldown enable) → SPECIALIST-NEGATIVE-IMPROVEMENT-FAIL; R1 catalog-CLOSED for SPECIALIST_mode
  - iter-v1/073: `feature-family` (ETH-IMPROVED-V2 feature-subset reduction 48→25 cols) → SPECIALIST-NEGATIVE-IMPROVEMENT-FAIL; dispersion-reservoir mechanism falsified
  - iter-v1/074: `risk-primitive` (ETH-IMPROVED-V3 AXIS-R Mid-Bull SHORT VETO post-aggregator rule layer) → currently active (no closeout yet)
  - iter-v1/075: `universe` (ATOM SPECIALIST EXPLORATION — first NEW SYMBOL mine) → active (no closeout yet)
- **Rotation status**: **VALID under the cycle-7 per-symbol regime-specialist mandate** (`feedback_v1_cycle6_per_symbol_regime_specialist_mandate.md` — axis-family rotation SUSPENDED for at least cycle-6+7; same symbol any number of times is permitted; NEW SYMBOL falls cleanly within the mandate). The /075 → /076 back-to-back `universe` mining is explicitly authorized by the user directive ("find new specialists … using all the quantitative knowledge" — mining mode).
- **One-sentence rationale**: BUNDLE-001's IS/OOS edge is concentrated in 3 symbols (DOT/ETH/BTC) with ~0.80 mean cross-asset correlation; AAVE is the ONLY eligible NEW SYMBOL passing the NEGATIVE-pooled-baseline gate cleanly (TS-mom (5,1) IS Sharpe −0.080 / (5,3) −0.127 — the DOT/063-precedent structural shape that was the necessary precondition for specialist edge extraction); the LOCKED 50-seed methodology has the highest mining-justified probability of extracting edge from this structural analog.

---

## Section 0.7 — SPECIALIST EXPLORATION 2-of-N for NEW SYMBOL mining

| Field | Value |
|---|---|
| **Mine-phase rank** | **2/N** (rank-2 in autopilot mining queue — DeFi-lending narrative first; rank-1 ATOM/075 is cosmos-interop) |
| **Cohort** | `("AAVEUSDT",)` — single-coin SPECIALIST (skill mandate; cycle-6+7 per-symbol regime-specialist mandate) |
| **Data extent** | 5.64y (2020-10-16 → 2026-06-06; 6178 8h candles) — second-longest in eligible set (after ATOM 6.33y); clears the 4y walk-forward floor by 41% |
| **Methodology constants HELD per user directive** | 50 inner seeds × 30 Optuna trials × `specialist_mode=True` + 48-col `V1_FEATURE_COLUMNS_PRUNED` + ATR (2.9, 1.45) + R1=OFF + R2=OFF + R3=ON-SHARED cutoff=0.70 + R5=ON + max_depth=5 FIXED + num_leaves=31 FIXED + n_estimators ≤ 500 + n_startup_trials=10 + mean-of-signed-weights aggregator. ENSEMBLE_SIZE=1. Outer seed=42. training_months=24. Walk-forward embargo `train_end_ms = test_start_ms - embargo_ms` (`5566a69`). |
| **The ONLY single-bit changes vs /063 dispatch** | (a) `SYMBOLS=("AAVEUSDT",)` (not DOTUSDT); (b) `ITERATION_LABEL="v1-076"`; (c) ATR pair (2.9, 1.45) — ETH/064 cell — matched to AAVE's ~95% IS realized vol regime (sits between ETH ~70% and DOT ~110%); (d) Model A wrapper (R1=OFF, R2=OFF; following ETH/064, BTC/065, ATOM/075 — NOT DOT/063's R1=ON+R2=ON Model E). All other constants byte-identical to the /063 → /064 → /065 → /075 SPECIALIST family. |
| **No parquet regeneration** | `data/features/AAVEUSDT_8h_features.parquet` exists (6178 × 230 cols, hash `209ab4c64667d051`); all 48 `V1_FEATURE_COLUMNS_PRUNED` columns are present. EDA table 09 reports NaN audit (Section 2.9). |
| **Anchor** | NONE — universe-extension. Verdict frame: ranked against BUNDLE-001 member IS Sharpe distribution (DOT/063 +0.43, ETH/064 +0.24, BTC/065 −0.18; mean +0.16, std ≈ 0.30). |
| **Strike framework** | N/A for first attempt — NEW SYMBOL EXPLORATION starts the strike counter at 0. If /076 verdicts PROMISING (any of the three PROMISING bands), AAVE enters BUNDLE-002 candidate roster; if NEGATIVE, AAVE is dropped after **ONE attempt** (positive-baseline trap precedent from /066 LINK, /067 LTC: one-attempt-and-eliminate for NEW SYMBOL universe extension to prevent knob-tuning a NEW SYMBOL into the cohort). |
| **Pre-registered verdict bands (HARD anti-tuning)** | Section 4 F-AXIS #1 bands frozen at this brief's commit (Section 12). Bands WILL NOT be re-tuned post-hoc. Per `feedback_no_cheating.md`. |

---

## Section 1 — Hypothesis

**H1 (PRIMARY)**: The locked SPECIALIST methodology (50 inner seeds × 30 Optuna trials, 48-col `V1_FEATURE_COLUMNS_PRUNED`, ATR(2.9, 1.45), R1=OFF / R2=OFF / R3=ON-SHARED cutoff=0.70, R5=ON, mean-of-signed-weights aggregator) — applied to AAVEUSDT — will produce a SPECIALIST IS Sharpe in the **PROMISING-TENTATIVE band [+0.20, +0.50]** (LM Master modal +0.20; QR-adjusted modal +0.16 after NaN-tax and ETH-leakage penalty), driven by the **NEGATIVE-pooled-baseline edge extraction mechanism**: AAVE's TS-mom (5,1) IS Sharpe −0.080 (table_06) is the ONLY eligible NEW SYMBOL passing the NEGATIVE-baseline gate cleanly, providing the structural DOT/063 precedent shape (DOT pre-/063 had a comparably negative TS-mom signal at the chosen lookback/horizon, and the 50-seed × 30-trial specialist methodology successfully extracted IS Sharpe +0.43 from that NEGATIVE precondition).

**H1a (mechanism — NEGATIVE-baseline gate as necessary precondition)**: The /066 LINK + /067 LTC ELIMINATIONS established the positive-baseline trap: when the trivial TS-mom IS Sharpe is already POSITIVE, the LightGBM head finds less marginal edge and underperforms BUNDLE membership. The mirror mechanism — that NEGATIVE-baseline is a PROMISING precondition — is the operating assumption for the AAVE mine. Table 06 shows AAVE's TS-mom at short horizons (5-bar lookback) is uniformly NEGATIVE: (5,1) −0.080, (5,3) −0.127, (5,5) −0.126, (5,10) −0.584. The deeper structure: AAVE's mid-lookback (20-bar) signals are POSITIVE (Sharpe +0.88 to +1.19 at horizons 1-5), while long-lookback (30-60 bar) are MIXED. This is a **non-monotone IS regime signature** — the short-horizon NEGATIVE-baseline opens a clean ML-edge surface that the 21-bar triple-barrier label can extract, while the mid-horizon POSITIVE structure provides the labeling backbone for the LightGBM to learn against. The /063 family at SPECIALIST budget specifically targets this non-monotone shape.

**H1b (mechanism — ATR(2.9, 1.45) vol-class match)**: AAVE's 2024 IS realized vol is 96.25% annualized + 2023 IS realized vol is 82.61% → **IS-weighted ~95% annualized** (table_02). Sits between ETH/064's regime (~70%) and DOT/063's regime (~110%) — same band as ATOM/075 (~80%). ATR(2.9, 1.45) is the ETH-class barrier pair; choosing it for AAVE is the **mechanism-matched cell** consistent with the /064 + /065 + /075 Model A pattern. This is a single-bit change vs /063's dispatch but is **methodology-compliant** — it slots AAVE into the same Model A `RiskV1Wrapper` cell as ETH/064, BTC/065, ATOM/075, preserving the cross-specialist comparability that BUNDLE-002 assembly will need.

**H1c (mechanism — Optuna + 50-seed averaging absorbs basin-lottery on a fresh symbol)**: Single-outer-seed=42 EXPLORATION exposes basin-lottery risk per `feedback_v1_basin_lottery_vigilance.md`; cycle-6/7 had 100% basin-lottery rate (4/4) on single-seed PROMISING tags. The 50-INNER-seed averaging (load-bearing SPECIALIST architecture) dampens within-cell basin-lottery substantially — σ_pop ≤ 0.30 was the F-AXIS #2 load-bearing gate at /063 and held at /064 / /065. For AAVE the 50-seed signal should similarly dampen the within-cell basin-lottery; verdict at single-outer-seed remains TENTATIVE per the basin-lottery vigilance rule.

**H1d (KEY RISK — ETH return correlation 0.75 IS / mechanism-overlap with ETH/064)**: Table 05 reports AAVE's IS rolling-90 ETH correlation **mean 0.745 / median 0.778 / p75 0.847** + full-IS-window ETH correlation **0.750**. This is the HIGHEST cross-asset correlation in the eligible NEW SYMBOL set and matches the user-prompt risk flag verbatim ("ETH corr 0.75 is the one risk — DeFi-cycle leakage to ETH/064"). Two compounding effects:
- (a) **Feature-level overlap**: 6-12 columns in `V1_FEATURE_COLUMNS_PRUNED` are `eth_*` cross-asset. AAVE's specialist signal will be PARTLY consuming the same `eth_ret_*` / `eth_rv_*` / `eth_vs_sym_*` patterns that ETH/064 already consumes for ETH itself. Mechanically, AAVE's model becomes a noisy proxy of ETH/064 → BUNDLE-002 inclusion risk: even if /076 specialist passes, the pair AAVE+ETH may fail the BUNDLE-002 mechanism-overlap check.
- (b) **Predicted-vs-actual lag**: AAVE-vs-ETH 0.75 corr means directional prediction synchronization on common features. The /076 specialist edge would be the residual signal — what AAVE adds BEYOND co-movement with ETH. The 50-seed × 30-trial budget operating on 48 features (of which 36-40 are within-symbol primitives) has reasonable headroom to extract this residual.

**Phase 7.4 mandatory diagnostic**: per-direction Sharpe + rolling-90day corr(AAVE_pred, ETH_pred) reporting. If corr(AAVE_pred, ETH_pred) ≥ 0.50, BUNDLE-002 assembly QR must treat /076 as **specialist-PROMISING-but-bundle-CONTESTED** — a verdict band that the BUNDLE-001 framework has not yet had to express. This is hardwired in Section 4 F-AXIS-FALSIFIER #2.

**H1e (KEY RISK — bull-IS / bear-OOS regime inversion → long-bias memorization → OOS collapse path)**: Table 08 reports AAVE IS yearly cumulative return: 2023 **+1.0947** (BULL), 2024 **+1.8378** (BULL), 2025-Q1 **−0.4007** (BEAR-IS-tail). The full-IS cumulative return is approximately **+13× compounded** — IS is overwhelmingly BULL-dominant. The OOS window (2025-03-24 → 2026-06-06) is structurally BEAR (LM Master cites OOS cumret −68.5%; consistent with the 2025-Q1 bear momentum continuing). This creates a **regime inversion**: IS is bull → triple-barrier labels skew LONG-favored → LightGBM at depth 5 may memorize the long-bias → OOS bear regime PUNISHES long-bias predictions → OOS Sharpe potentially deeply negative even if IS clears +0.20. The mitigation stack:
- (a) 50-seed averaging dampens single-seed bear-fit basins but does NOT eliminate consistent bull-bias across seeds.
- (b) R3=ON-SHARED cutoff=0.70 OOD filter will fire heavily on OOS bear-regime trades — defending Sharpe but at the cost of trade count.
- (c) Phase 7.4 post-mortem MUST report per-direction (long/short) Sharpe + trade count + WR. Direction-asymmetric Sharpe > 1.5σ favoring longs in IS is the fingerprint of long-bias memorization.

This is structurally the **INVERSE** of /075 ATOM's risk (which was bear-IS + bear-OOS — directional parity favoring SHORTS). For /076, the LONG-bias memorization is the modal failure mode.

**H1f (table_07 — SL-heavy label distribution)**: Triple-barrier labels under ATR(2.9, 1.45) at horizon=21 are **SL-heavy on BOTH sides** (LONG SL 57.8%, SHORT SL 58.8%) — typical of high-vol assets at TP/SL ratio 2.0:1. The 25.7% LONG-TP rate vs 23.4% SHORT-TP rate suggests a mild long-favored label asymmetry (consistent with H1e bull-IS) — only 2.3 percentage points of long-vs-short TP asymmetry, NOT a catastrophic asymmetry. At ratio=2.0, the probabilistic break-even WR is 33.3% (TP payoff is 2× SL loss). The LightGBM head must learn directional accuracy significantly above 33.3% on EITHER side to produce +EV trades.

**Net**: AAVE is a MEDIUM-LOW-confidence PROMISING-TENTATIVE candidate. The NEGATIVE-baseline edge mechanism is the strongest structural signal in the eligible NEW SYMBOL set (DOT/063 precedent shape); two HIGH-severity compounding risks pull the modal IS prediction down: (1) ETH-leakage 0.75 → mechanism-overlap with ETH/064 + bundle-level rejection risk; (2) bull-IS / bear-OOS regime inversion → long-bias memorization → modal OOS collapse path.

**Modal predicted IS Sharpe**: **+0.20** (LM Master Phase 4.5 modal); 60% band [0.0, +0.40]; 90% band [−0.20, +0.55]. **Modal predicted OOS Sharpe**: −0.10 (LM Master Phase 4.5 modal); wider band [−0.40, +0.30].

---

## Section 2 — IS-Only Numerical Evidence (from `analysis/v1-076/eda.py`)

**Analysis script**: `analysis/v1-076/eda.py` (committed at brief authoring; IS-firewall verified by path-substring assertion `_assert_is_only_path` and IS-filter `is_only(df)` applied to every klines load).
**Source data**:
- `data/AAVEUSDT/8h.csv` (6178 rows total; 2160 IS rows; OOS rows present but filtered out at usage)
- `data/features/AAVEUSDT_8h_features.parquet` (6178 × 230 cols; 48 `V1_FEATURE_COLUMNS_PRUNED` present; opened ONLY for NaN audit in table_09)
- Anchor klines for cross-asset corr: `data/{BTCUSDT,ETHUSDT,DOTUSDT,LTCUSDT,LINKUSDT}/8h.csv`

All tables are persisted to `analysis/v1-076/*.csv` and re-derivable by `uv run python analysis/v1-076/eda.py`.

### 2.1 Data extent (table_01) — AAVE clears 4y walk-forward floor

| symbol | first_open | last_open | total_8h | IS_candles | years_total |
|---|---|---|---:|---:|---:|
| **AAVEUSDT** | **2020-10-16** | 2026-06-06 | 6178 | **2160** | **5.64** |
| BTCUSDT | 2020-01-01 | 2026-06-01 | 7030 | 2160 | 6.41 |
| ETHUSDT | 2020-01-01 | 2026-06-01 | 7030 | 2160 | 6.41 |
| DOTUSDT | 2020-08-22 | 2026-05-27 | 6313 | 2160 | 5.76 |
| LTCUSDT | 2020-01-09 | 2026-06-01 | 6991 | 2160 | 6.39 |
| LINKUSDT | 2020-01-17 | 2026-05-27 | 6966 | 2160 | 6.36 |

AAVE has **5.64y of 8h candles** — second-longest in the eligible NEW SYMBOL set (after ATOM 6.33y) and exceeds the 4y walk-forward floor by 41%. The IS window covers 2160 candles (24 months @ 8h cadence × 30d/mo × 3 candles/day ≈ 2160 expected — exact match, identical to all v1 native cohorts).

### 2.2 Realized vol regime by IS year (table_02) — ETH-class to DOT-class mid-vol

| year | rows | ann_realized_vol_pct | natr_30_median |
|---|---:|---:|---:|
| 2020 (Q4 only) | 231 | 164.22% | 0.0754 |
| 2021 | 1095 | 150.27% | 0.0638 |
| 2022 | 1095 | 118.63% | 0.0522 |
| **2023** | 1095 | **82.61%** | 0.0345 |
| **2024** | 1098 | **96.25%** | 0.0417 |
| **2025-Q1** | 246 | **119.80%** | 0.0572 |

**IS-window weighted avg ≈ 95% annualized** — sits between ETH (~70%) and DOT (~110%), comparable to ATOM (~80%) but slightly higher. This is the mechanism-rational justification for choosing the ETH/064 ATR cell (2.9, 1.45) over DOT/063's (3.5, 1.75): AAVE's vol regime supports the moderate-TP/tight-SL pair. The 2024 → 2025-Q1 transition (96 → 120%) shows vol-regime EXPANSION approaching the OOS window — consistent with the OOS bear-regime transition (LM Master Risk Flag 2). Vol-regime expansion at OOS-handover is a modest stationarity concern but is within the 50-seed averaging's tolerance band; mitigation via R3 OOD gate.

### 2.3 Rolling 100-bar Hurst exponent (table_03)

**DIAGNOSTIC ONLY — the rolling-Hurst implementation in `_hurst_simple` is the rescaled-range-on-log-returns variant which is known to be biased toward 0 on noisy financial returns; observed values [−0.11, +0.09] are NOT Hurst-interpretable**. The LM Master Phase 4.5 advisor cites Hurst≈0.52 (near random walk) from a separate computation (full-window log-price R/S exponent; different algorithm). This brief defers to the LM Master Phase 4.5 estimate for Hurst-regime narrative (AAVE near random walk → ML edge cannot rely on simple persistence/MR). The EDA table_03 is retained for reproducibility but NOT cited as Hurst evidence in Section 1.

### 2.4 Regime mix (table_04) — chop-dominant but more balanced than ATOM

| regime (50-bar return ±15%) | frac | count |
|---|---:|---:|
| **chop** (|ret_50| ≤ 0.15) | **54.3%** | 2612 |
| **bull** (ret_50 > 0.15) | **25.1%** | 1205 |
| **bear** (ret_50 < −0.15) | **20.6%** | 993 |

All 3 regimes are represented in the IS window — no zero-regime bucket. Chop-dominant 54% (lower than ATOM's 58%) with stronger bull representation (25% vs ATOM's 22%) — modestly bull-tilted regime distribution. LM Master's separate citation of 32/28/39 (bull/bear/chop) using a different ret_50 threshold gives a more bull-heavy view; both characterizations agree that **AAVE has the best-balanced regime distribution** in the eligible NEW SYMBOL set. The 48-col stack carries mean-reversion primitives (`vwap_dev_*`, `mr_bb_pctb_*`, `mr_rsi_extreme_*`) and momentum/trend primitives (`mom_macd_*`, `trend_adx_*`, `trend_supertrend_*`) that should cover the bull-heavy regime distribution.

### 2.5 Cross-asset rolling-90 return correlation (table_05) — ETH 0.75 LOAD-BEARING RISK CONFIRMED

| anchor | rolling_90 mean | rolling_90 median | rolling_90 p75 | full IS corr |
|---|---:|---:|---:|---:|
| BTCUSDT | 0.649 | 0.695 | 0.785 | 0.635 |
| **ETHUSDT** | **0.745** | **0.778** | **0.847** | **0.750** |
| DOTUSDT | 0.703 | 0.723 | 0.820 | 0.679 |
| LTCUSDT | 0.639 | 0.639 | 0.755 | 0.637 |
| LINKUSDT | 0.702 | 0.721 | 0.809 | 0.708 |

**AAVE's IS rolling-90 ETH correlation mean is 0.745 / median 0.778 — the HIGHEST in the eligible NEW SYMBOL set and the LOAD-BEARING risk for /076**. The user prompt explicitly flagged this: "ETH corr 0.75 is the one risk — DeFi-cycle leakage to ETH/064 — flag for QR feature-importance review post-EXPLORATION." This brief HARDWIRES the diagnostic into Section 4 F-AXIS-FALSIFIER #2 (rolling-90day corr(AAVE_pred, ETH_pred) at Phase 7.4). The AAVE-vs-BTC IS corr 0.635 is moderate (lower than ATOM's 0.617 by a hair); AAVE-vs-DOT 0.679 is comparable. **The single load-bearing concern is the ETH leakage** — flagged for BUNDLE-002 assembly + Phase 7.4 importance triage.

### 2.6 TS-mom IS Sharpe baseline grid (table_06) — NEGATIVE-BASELINE GATE PASSES CLEANLY AT SHORT HORIZONS

| lookback | horizon | n_obs | ann_sharpe_IS | long_frac | short_frac |
|---:|---:|---:|---:|---:|---:|
| **5 | 1** | 4854 | **−0.0796** | 0.503 | 0.496 |
| **5 | 3** | 4852 | **−0.1265** | 0.503 | 0.496 |
| **5 | 5** | 4850 | **−0.1261** | 0.503 | 0.496 |
| **5 | 10** | 4845 | **−0.5840** | 0.503 | 0.496 |
| 10 | 1 | 4849 | +0.3993 | 0.506 | 0.493 |
| 10 | 3 | 4847 | +0.3232 | 0.506 | 0.493 |
| 10 | 5 | 4845 | +0.3161 | 0.506 | 0.493 |
| 10 | 10 | 4840 | −0.3895 | 0.506 | 0.493 |
| **20 | 1** | 4839 | **+0.8827** | 0.515 | 0.485 |
| **20 | 3** | 4837 | **+1.1281** | 0.515 | 0.485 |
| **20 | 5** | 4835 | **+1.1925** | 0.515 | 0.485 |
| 20 | 10 | 4830 | +0.4571 | 0.515 | 0.485 |
| 30 | 1 | 4829 | +0.0750 | 0.507 | 0.493 |
| 30 | 3 | 4827 | −0.2771 | 0.507 | 0.493 |
| 30 | 5 | 4825 | −0.2584 | 0.507 | 0.493 |
| **30 | 10** | 4820 | **−0.9751** | 0.507 | 0.493 |
| 60 | 1 | 4799 | +0.2756 | 0.510 | 0.490 |
| 60 | 3 | 4797 | +0.5929 | 0.510 | 0.490 |
| 60 | 5 | 4795 | +0.6049 | 0.510 | 0.490 |
| 60 | 10 | 4790 | +0.3381 | 0.510 | 0.490 |

**KEY OBSERVATIONS**:

- **Short-horizon (5-bar lookback)**: UNIFORMLY NEGATIVE Sharpe (−0.08 to −0.58) — **the NEGATIVE-pooled-baseline gate passes cleanly**. This is the DOT/063-precedent structural shape and is the strongest single-lens advantage AAVE has in the eligible set.
- **Mid-lookback (20-bar)**: STRONG POSITIVE Sharpe (+0.88 to +1.19) — a 5-day to 1-day-trend signal is structurally embedded in the IS data. This is the BACKBONE for the LightGBM to learn against — the 21-bar triple-barrier label sits squarely on this signal's horizon.
- **Long-lookback (30-bar)**: MIXED to NEGATIVE (−0.98 at 30/10) — long trends INVERT at the 10-bar horizon.
- **Direction balance**: roughly 50/50 long/short across all rows; mild long-tilt at 20-bar lookback (51.5% long) — consistent with the bull-leaning IS regime.

**NEGATIVE-baseline gate classification**: AAVE PASSES cleanly on the short-horizon (5-bar) basis. The (5,1) Sharpe −0.080 is the structural DOT/063-precedent shape that the /066 LINK and /067 LTC ELIMINATIONS established as the necessary precondition for specialist edge extraction (those had STRONG positive baselines at the equivalent lookback/horizon). **Non-monotone IS regime shape**: short-horizon NEGATIVE + mid-horizon POSITIVE + long-horizon MIXED — this is the load-bearing structural signature that the 21-bar triple-barrier + LightGBM head should be able to extract.

**Mine-phase formula vs LM Master replication discrepancy**: the chosen-symbol rationale cited TS-mom IS Sharpe −0.311; LM Master replicated −0.124 at mom_5/fwd_3; this brief's table_06 gives (5,1) −0.080 and (5,3) −0.127. All three numbers agree on the SIGN (negative) and the order of magnitude. The exact value depends on the specific (lookback, horizon) and the windowing convention; the substance — NEGATIVE-baseline gate passes — is robust across all three replications.

### 2.7 Triple-barrier label distribution at ATR(2.9, 1.45), horizon=21 (table_07) — SL-HEAVY ON BOTH SIDES, MILD LONG TILT

| side | n_labels | tp_frac | sl_frac | timeout_frac |
|---|---:|---:|---:|---:|
| **LONG** | 4826 | 25.74% | **57.79%** | 16.47% |
| **SHORT** | 4826 | 23.41% | **58.79%** | 17.80% |

Triple-barrier labels under ATR(2.9, 1.45) are **SL-heavy on both sides** (LONG 58% SL, SHORT 59% SL) — typical of high-vol assets at TP/SL ratio 2.0:1. The 25.7% LONG-TP vs 23.4% SHORT-TP shows a **mild 2.3pp long-favored TP asymmetry** — consistent with the bull-leaning IS regime (table_08). At ratio=2.0, the probabilistic break-even WR is 33.3%; observed 25.7% LONG-TP requires directional accuracy ABOVE 33.3% on the long side to produce +EV trades. The LightGBM head's task is precisely this directional separation.

**Comparison to ATOM/075 same cell**: ATOM had LONG SL 59.95% / SHORT SL 55.17% — mildly SHORT-favored label asymmetry. AAVE inverts this with LONG SL 57.79% / SHORT SL 58.79% — mild LONG-favored label asymmetry. Both are within 3 percentage points symmetric, NOT a catastrophic asymmetry. The Phase 7 evaluation MUST report per-direction Sharpe to disambiguate whether the realized IS Sharpe is broad-based or direction-bias mirage (per Section 4 F-AXIS-FALSIFIER #1).

### 2.8 Per-direction regime audit (table_08) — DEEP-BULL-IS in last 24 months — LONG-BIAS MEMORIZATION RISK CONFIRMED

| year | bars | year_cum_return | implied_directional_bias |
|---|---:|---:|---|
| 2020 (Q4 only) | 231 | +1.1461 | BULL |
| 2021 | 1095 | +1.8686 | BULL |
| 2022 | 1095 | −0.7955 | BEAR |
| **2023** | 1095 | **+1.0947** | BULL |
| **2024** | 1098 | **+1.8378** | BULL |
| **2025-Q1** | 246 | **−0.4007** | BEAR |

The **IS window (2023+2024+2025-Q1) is BULL → BULL → BEAR cumulative**. The cumulative IS return (2023+2024+2025-Q1) is approximately **+13×** compounded (1+1.09 × 1+1.84 × 1−0.40 ≈ 3.76) — **deep-bull IS with bear-Q1 tail**. The LM Master Risk Flag 2 is **CONFIRMED**: triple-barrier labels in IS will skew toward direction=+1 hits → LightGBM at depth 5 may memorize the long-bias → OOS bear regime PUNISHES long-bias predictions. The Phase 7 evaluation MUST report per-direction Sharpe (long vs short) to flag long-bias mirage; if observed IS Sharpe ≥ +0.20 with >70% of trades in direction=+1, downgrade to NEGATIVE-LONG-BIAS-MIRAGE per Section 4 falsifier.

**Structural inverse vs /075 ATOM**: ATOM had 2024+2025-Q1 cumulative IS ≈ −0.51 (BEAR → BEAR-EXTENSION). AAVE has 2024+2025-Q1 cumulative IS ≈ +0.70 (BULL → BEAR-TAIL). For ATOM the bias was SHORT-mirage; for AAVE the inverse risk is LONG-mirage. Both directions are within the F-AXIS-FALSIFIER #1 falsifier shape — only the failure-mode direction is flipped.

### 2.9 Feature 48-col NaN audit (table_09) — 2 columns ALL-NaN-IS by symbol-conditioning + funding cols mildly NaN

| feature | is_nan_frac | oos_nan_frac | verdict |
|---|---:|---:|---|
| `dot_vs_btc_ret_ratio_30` | **1.0000** | 1.0000 | ALL-NaN — SYMBOL-conditional (only populated for SYMBOL=DOT) |
| `eth_vs_btc_ret_ratio_30` | **1.0000** | 1.0000 | ALL-NaN — SYMBOL-conditional (only populated for SYMBOL=ETH) |
| `long_short_zscore_30` | 0.4311 | 0.0000 | HIGH-NaN-IS — long/short data starts mid-window for AAVE |
| `oi_delta_30_z90` | 0.3412 | 0.0000 | HIGH-NaN-IS — OI data starts mid-window for AAVE |
| `btc_funding_spread_30_90` | 0.0241 | 0.0448 | MINOR-HEAD-NaN-IS |
| `regime_momentum_signed_5d` | 0.0204 | 0.0000 | MINOR-HEAD-NaN-IS |
| `funding_rate_zscore_90` | 0.0187 | 0.0448 | MINOR-HEAD-NaN-IS |
| `vol_range_spike_72` | 0.0146 | 0.0000 | MINOR-HEAD-NaN-IS |
| `funding_rate_zscore_30` | 0.0117 | 0.0448 | MINOR-HEAD-NaN-IS |
| 39 other features | 0.0000-0.0103 | 0.0000-0.0050 | CLEAN to MINOR-HEAD |

**Impact assessment**:
- **`dot_vs_btc_ret_ratio_30` + `eth_vs_btc_ret_ratio_30` ALL-NaN** — IDENTICAL pattern to ATOM/075 (these features are SYMBOL-conditional within V1 feature-generation code — populated only for SYMBOL=DOT / SYMBOL=ETH respectively). LightGBM handles NaN natively (`use_missing=True` default); the two features rank effectively at zero-importance for AAVE. **Magnitude**: 2 of 48 = 4.2% of colsample_bytree slots wasted. Adjustment to predicted IS Sharpe: ≈ −0.02 to −0.05.
- **`long_short_zscore_30` and `oi_delta_30_z90` ~34-43% NaN in IS**: AAVE-specific long/short and OI data starts mid-IS-window (~mid-2024). Same LightGBM NaN handling; partial coverage means partial signal. Adjustment: ≈ −0.02.
- **`funding_rate_zscore_30/90` clean at 1-2% head-NaN**: LM Master Risk Flag 5 (funding rate early-window gaps) is **REFUTED at IS** — only 57-91 NaN rows out of 4860 IS rows = 1.2-1.9% head-NaN, which is the standard warm-up tail for a rolling window. Funding rate features populate cleanly for AAVE. Adjustment: 0 (refuted risk).
- **Net adjusted predicted IS Sharpe**: LM Master modal +0.20 − 0.04 (wasted-slot tax) ≈ **+0.16 modal QR-adjusted** (still inside PROMISING-TENTATIVE band low end).

### 2.10 Cross-cohort return-corr pyramid (table_10) — AAVE's bundle-position

| pair | n_overlap_IS | ret_corr_IS | diversity_score |
|---|---:|---:|---:|
| AAVE-vs-BTC | 4859 | **0.6348** | **0.3652** |
| AAVE-vs-LTC | 4844 | 0.6374 | 0.3626 |
| AAVE-vs-DOT | 4859 | 0.6790 | 0.3210 |
| AAVE-vs-LINK | 4859 | 0.7078 | 0.2922 |
| **AAVE-vs-ETH** | 4859 | **0.7504** | **0.2496** |

AAVE-vs-BTC IS corr 0.635 / diversity_score 0.365 is the **highest diversity score** in the AAVE pyramid (the most idiosyncratic anchor pairing) — AAVE-vs-LTC at 0.637 is essentially tied. Both are modestly LESS diverse than ATOM-vs-BTC (which had IS corr 0.617). **The AAVE-vs-ETH IS corr 0.750 is the LOWEST diversity in the pyramid and the LOAD-BEARING bundle-overlap risk**: at 0.75 ETH correlation, AAVE+ETH BUNDLE-002 inclusion will face the rolling-90day prediction-correlation check (`feedback_v1_bundle_no_coin_overlap.md` mandates coin-pair non-overlap; mechanism-overlap at 0.75 raw-return correlation is a softer flavor and is checked at PREDICTION-correlation NOT raw-return correlation in BUNDLE-002 assembly). **This is flagged for downstream (BUNDLE-002 assembly), not /076 EXPLORATION blocker**.

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1)

- **Declaration**: **HIGH-RISK**
- **Reason**: NEW SYMBOL universe-extension is a structural change to Optuna's training-objective domain — the loss surface, label distribution, and feature-importance ranking are all changed because a brand-new symbol's data and regime history have never been training-objective for any v1 specialist. This qualifies as a HIGH-RISK axis under the Section 2.5 rubric (v1 refactor) because the change is **universe substitution** — explicitly listed as a HIGH-RISK trigger. Additionally, the AAVE-specific risk profile (HIGH ETH-leakage 0.75 + HIGH bull-IS/bear-OOS regime inversion) elevates the failure-mode probability above the typical NEW SYMBOL EXPLORATION.
- **Mitigation**: **single-seed=42 EXPLORATION** with 50-INNER-seed averaging (the load-bearing SPECIALIST architecture — σ_pop ≤ 0.30 has historically held). Multi-outer-seed validation is **DEFERRED** to a subsequent iteration if /076 verdicts PROMISING and is flagged by `feedback_v1_basin_lottery_vigilance.md` triggers (per-seed spread > 0.50 OR Jaccard < 0.40 OR Spearman ρ < 0.50). Under the v1 rule, if 3+ consecutive HIGH-RISK single-seed EXPLORATIONs produce >1σ negative deltas in a row, the next becomes mandatorily multi-seed; /072, /073 produced >1σ NEG; /074 verdict pending; /075 verdict pending. If /074 + /075 + /076 close NEG, then /077 becomes mandatorily multi-seed.
- **NEW SYMBOL strike rule (one-attempt-and-eliminate)**: per /066 LINK and /067 LTC precedent, NEW SYMBOL universe extension at SPECIALIST EXPLORATION budget has a ONE-ATTEMPT rule. If /076 closes NEGATIVE (any of the four NEGATIVE bands), AAVE is dropped from the BUNDLE-002 candidate roster after this single EXPLORATION. The mining axis pivots to rank-3 candidate.
- **Why not bundle ATR-pair shift with a second knob**: identical reasoning to /075 — methodology-COMPLIANT single-bit discipline is the load-bearing verdict-integrity guarantee. Any second knob (HP tweak, n_trials shift, label horizon shift, feature subset) would break the single-bit discipline and make the verdict uninterpretable.

---

## Section 3 — Proposed Changes (single-bit dispatch deviation from /063 family)

### 3.1 Code-level changes

**(a) Runner: clone `run_iteration_063.py` → `run_iteration_076.py`** with identical signature, except:
- `ITERATION_LABEL = "v1-076"` (was `"v1-063"`)
- `ITERATION_NUMBER = 76` (was 63)
- The runner docstring updated to reflect AAVE SPECIALIST and ETH-class ATR cell (2.9, 1.45) instead of DOT's (3.5, 1.75)
- `--symbols AAVEUSDT` (was `--symbols DOTUSDT`)
- FEATURES_BASE_HASH_48COL: identical sha256(`V1_FEATURE_COLUMNS_PRUNED`) hash (`b81176f893826500536ec5cee8ad00e74bf7edb834290e62e835213defe74ca3` — 48-col stack UNCHANGED)

**(b) Dispatch: add `V1_ITER076_UNIVERSE: tuple[str, ...] = ("AAVEUSDT",)` to `features_v1/__init__.py`** with parallel docstring to V1_ITER075_UNIVERSE / V1_ITER065_UNIVERSE.

**(c) Dispatch: add `elif iteration_label == "v1-076" and set(symbols) == set(V1_ITER076_UNIVERSE):`** branch in `run_baseline_v1.py`, byte-identical to the `v1-075` ATOM SPECIALIST branch except for:
- Universe assertion: `assert set(symbols) == {"AAVEUSDT"}` (was `{"ATOMUSDT"}`)
- Model wrapper instance name: `Model_A_AAVE_specialist_076` (was `Model_A_ATOM_specialist_075`)
- `BacktestConfig(symbols=("AAVEUSDT",), ...)` (was `("ATOMUSDT",)`)
- All other kwargs: byte-identical to /075 (ATR(2.9, 1.45), R1=OFF, R2=OFF, R3=ON-SHARED cutoff=0.70, R5=ON vt_target_vol=0.3 vt_lookback_days=45 vt_min_scale=0.33, specialist_mode=True, V1_SPECIALIST_SEED_COUNT=50, V1_SPECIALIST_OPTUNA_TRIALS=30, max_depth=5 FIXED, num_leaves=31 FIXED, n_estimators ≤ 500, n_startup_trials=10, mean-of-signed-weights aggregator, training_months=24)

**(d) Pre-flight guard** (mirrors /075): assert `_compute_features_hash(V1_FEATURE_COLUMNS_PRUNED) == FEATURES_BASE_HASH_48COL` at runner entry; assert `len(active_feature_columns) == 48`; assert `set(symbols) == {"AAVEUSDT"}`; assert `V1_SPECIALIST_SEEDS[0] == 42` and `V1_SPECIALIST_SEEDS[-1] == 91`.

**(e) Engine parity (HARD per `feedback_v1_backtest_live_parity_hard.md`)**: NEW SYMBOL universe extension propagates to `engine.py:_initial_setup` symbol-fetch (must add AAVEUSDT to the kline-fetch list when a BUNDLE-002 with AAVE merges). For /076 EXPLORATION only, the BACKTEST runner is the validation surface; the engine parity is verified at BUNDLE-002 assembly time, NOT at /076. The Critic Check 15 = `BUNDLE-PARITY-VIOLATION` is **N/A at /076 EXPLORATION** (no bundle assembly).

### 3.2 What is held identical to /063 / /064 / /065 / /075 (everything except the universe identity)

| Variable | Value |
|---|---|
| Universe | `{AAVEUSDT}` (single-coin SPECIALIST) |
| Feature columns | **`V1_FEATURE_COLUMNS_PRUNED` (48 cols, UNCHANGED)** — sha256 hash `b81176f893826500536ec5cee8ad00e74bf7edb834290e62e835213defe74ca3` |
| Labels | Triple-barrier **ATR TP=2.9 / ATR SL=1.45** (ETH/064 cell — Model A match) |
| Label horizon | 21 candles (UNCHANGED) |
| Optuna trials | **30** (UNCHANGED) |
| Inner ensemble seeds | **50** (`specialist_mode=True`; UNCHANGED — V1_SPECIALIST_SEEDS = 42..91) |
| ENSEMBLE_SIZE | 1 (UNCHANGED) |
| Outer seed | 42 (single EXPLORATION ply; UNCHANGED) |
| max_depth | 5 FIXED (UNCHANGED) |
| num_leaves | 31 FIXED (UNCHANGED) |
| n_estimators | ≤500 (UNCHANGED) |
| n_startup_trials | 10 (UNCHANGED) |
| Aggregator | mean-of-signed-weights (UNCHANGED) |
| training_months | 24 (sacred; UNCHANGED) |
| Walk-forward embargo | `train_end_ms = test_start_ms - embargo_ms` (commit `5566a69`; UNCHANGED) |
| Model wrapper class | **Model A** (`RiskV1Wrapper` with R1=OFF, R2=OFF, R3=ON-SHARED cutoff=0.70) — matches /064 ETH, /065 BTC, /075 ATOM; NOT /063 DOT's Model E |
| Vol targeting | Per-coin VT (45-day rolling, target_vol=0.3, min_scale=0.33, max_scale=2.0; UNCHANGED) |
| Parquet feature-generation | **NO REGENERATION** — `data/features/AAVEUSDT_8h_features.parquet` exists with all 48 V1_FEATURE_COLUMNS_PRUNED present (table_09 audit). |

### 3.3 What is NOT changed (per LOCKED methodology directive)

- **No feature change** (V1_FEATURE_COLUMNS_PRUNED stays at 48 cols — sha256 hash UNCHANGED; the 2 ALL-NaN-IS columns are LightGBM-native-NaN-handled, not removed)
- **No labeling change** (triple-barrier ATR=2.9/1.45 — Model A cell consistent with /064 /065 /075)
- **No model-arch change** (LightGBM head; not XGBoost; per /016 v3 closure)
- **No risk-wrapper flip** (R1 stays OFF per `f81cafc3` catalog rule + Model A pattern; R2 stays OFF; R3 stays ON-SHARED cutoff=0.70; R5 stays ON)
- **No Optuna search-space change** (HP bounds inherited from /063 family; bounds_profile="v1_specialist")
- **No multi-seed promotion** (single outer seed=42 EXPLORATION discipline; multi-seed deferred to a future CONFIRMATION if /076 PROMISING)
- **No parquet regeneration** (HIGH guard: cross-iteration reproducibility for /077+ mining pipeline depends on parquet hash stability)
- **No post-aggregator rule layer** (the /074 AXIS-R Mid-Bull SHORT VETO is structurally INVERSE for AAVE — AAVE IS is bull-dominant + bear-tail; the mid-bull SHORT VETO would BLOCK shorts in mid-bull which is the wrong direction. /074's rule is NOT applied to /076)
- **No threshold tuning** (Optuna picks `confidence_threshold` per seed within the locked range [0.50, 0.85])
- **No ETH-leakage feature exclusion** (per LM Master: feature-stack changes destabilize cross-seed dispersion at SPECIALIST mode; the 0.75 ETH corr risk lives at BUNDLE-002 assembly, NOT at /076 EXPLORATION)

### 3.4 Response to LM Master Phase 4.5 recommendations (per v1 LM Coordination)

LM Master's `briefs-v1/iteration_v1-076/lgbm_advisor.md` is a SCOPE-CONSTRAINED advisor — methodology constants are LOCKED per user directive, so LM Master's "Recommended Hyperparameter Direction" section is observation-only (no actionable HP changes). QR response:

| LM Master section | QR response |
|---|---|
| Recommended HP direction #1: verify single-coin cohort `(AAVEUSDT,)` and ITERATION_LABEL="v1-076" | **ADOPTED VERBATIM** — Section 3.1 (a)-(c) implements the exact dispatch. |
| Recommended HP direction #2: observe `n_estimators` realized distribution at Phase 7.4 (bimodal expected; chop ~250, directional ~450) | **ADOPTED** — Phase 7.4 post-mortem will report best-trial `n_estimators` across walk-forward months. Std > 150 across months = expected per LM mechanism, NOT basin-lottery alarm. |
| Recommended HP direction #3: `min_data_in_leaf` and `lambda_l1` at Phase 7.4 (long-bias memorization fingerprint: min_data_in_leaf < 50 for >40% of months AND long-Sharpe asymmetry > 1.5σ) | **ADOPTED** — Phase 7.4 post-mortem will flag this fingerprint. |
| Recommended feature-engineering direction: verify `regime_momentum_signed_5d`, `hurst_100`, `vwap_dev_20` populate cleanly; verify `eth_ret_*`, `eth_rv_*`, `eth_vs_sym_*` non-NaN | **VERIFIED** in table_09 — `regime_momentum_signed_5d` 2.0% head-NaN (CLEAN); `funding_rate_zscore_30/90` 1.2-1.9% head-NaN (CLEAN; LM Risk Flag 5 REFUTED); ETH cross-asset features all populate cleanly; the 2 SYMBOL-conditional ratio features ALL-NaN (LightGBM NaN-handles). |
| Predicted modal IS Sharpe +0.20; 90% band [−0.20, +0.55] | **ADOPTED** as the F-AXIS #1 verdict band reference (modal +0.20); per QR table_09 NaN-tax adjustment, MQR-modal-adjusted = +0.16. |
| Risk Flag 1: ETH corr 0.75 IS / 0.80 OOS → DeFi-cycle leakage to ETH/064 (HIGH) | **HARDWIRED as F-AXIS-FALSIFIER #2** — Section 4 mandates rolling-90day corr(AAVE_pred, ETH_pred) at Phase 7.4; BUNDLE-002 assembly mandate to check pair pred-corr. |
| Risk Flag 2: bull-IS / bear-OOS regime inversion → long-bias memorization → OOS collapse (HIGH) | **HARDWIRED as F-AXIS-FALSIFIER #1** — Section 4 mandates per-direction (long/short) Sharpe + trade count + WR; if >70% trades direction=+1 AND long-Sharpe > short-Sharpe + 1.5σ, downgrade to NEGATIVE-LONG-BIAS-MIRAGE. |
| Risk Flag 3: IS realized vol 118% > DOT cluster — high-vol concentration (MEDIUM) | **ACKNOWLEDGED, downstream BUNDLE-002 concern**. /076 is single-coin SPECIALIST; vol concentration is a BUNDLE-LEVEL risk that applies at BUNDLE-002 assembly time. Not a /076 blocker. |
| Risk Flag 4: mine-phase TS-mom Sharpe −0.311 differs from replication −0.124 (LOW) | **DOCUMENTED in Section 2.6** — all three replications (mine −0.311, LM −0.124, QR table_06 (5,1) −0.080) agree on SIGN; NEGATIVE-baseline gate passes robustly across formulas. |
| Risk Flag 5: funding rate early-window gaps (LOW) | **REFUTED via table_09** — funding_rate_zscore_30/90 are at 1.2-1.9% head-NaN (rolling-window warm-up), NOT all-NaN. The risk is empirically REFUTED. |
| Saturation Risk 1: Second NEW SYMBOL mine — DeFi narrative duplication starts. After /076, do NOT pull another DeFi-lending symbol in /077 | **ADOPTED** for autopilot queue: /077+ should rotate to non-DeFi narrative cluster (storage / interoperability / payments). Pre-registered for orchestrator. |
| Saturation Risk 2: 0.80 OOS ETH corr — BUNDLE-002 must use AAVE OR ETH, not both | **ADOPTED** — BUNDLE-002 assembly mandate; the AAVE-vs-ETH pair check is HARDWIRED at BUNDLE-002. |
| Saturation Risk 3: No prior LM Master calibration on NEW SYMBOL mining; +0.20 modal is mechanism-derived not frequentist (MEDIUM-LOW confidence) | **ACCEPTED** — Section 4 bands are pre-registered relative to the BUNDLE-001 specialist IS Sharpe distribution (mean +0.16, std ≈ 0.30), NOT relative to the LM Master modal alone. The bands are robust to LM Master prediction error within ~±0.20. |
| Saturation Risk 4: Basin-lottery vigilance applies even at 50-inner-seed | **ADOPTED** — Section 4 F-AXIS #2 σ_pop dispersion gate. |
| Closing note: per-direction Sharpe + AAVE/ETH prediction correlation reporting at Phase 7.4 | **HARDWIRED** — Section 4 F-AXIS-FALSIFIER #1 + #2 explicit; the verdict cannot be cleanly interpreted without these two diagnostics. |

LM Master confidence: **MEDIUM-LOW**. QR concurs on MEDIUM-LOW confidence; the brief is honest about the bull-IS/bear-OOS regime inversion (HIGH risk) and the 0.75 ETH-leakage (HIGH risk). The NEGATIVE-baseline gate edge partially compensates but the failure-mode space is structurally larger than ATOM/075.

---

## Section 4 — F-Axis Bands (Falsifier Gates)

Pre-registered F-AXIS bands per `feedback_no_cheating.md` (HARD anti-tuning — frozen at brief commit SHA Section 12). Band edges WILL NOT be re-tuned post-hoc under any scenario.

### F-AXIS #1 — Mean IS Sharpe across 50 inner seeds (PRIMARY verdict; PROMISING / NEGATIVE adjudicator)

Anchor: NEW SYMBOL — no prior AAVE specialist; bands referenced against the BUNDLE-001 member IS Sharpe distribution and the LM Master Phase 4.5 modal +0.20.

| Band | Range (mean IS Sharpe) | Verdict | Action |
|---|---|---|---|
| **PROMISING-CLEAN** | **IS Sharpe ≥ +0.50** | SPECIALIST-PROMISING-STRONG | AAVE enters BUNDLE-002 candidate roster at HIGH confidence (PENDING AAVE-vs-ETH pair check, F-AXIS-FALSIFIER #2); multi-outer-seed CONFIRMATION queued. |
| **PROMISING-TENTATIVE** | **+0.20 ≤ IS Sharpe < +0.50** | SPECIALIST-PROMISING-TENTATIVE | AAVE enters BUNDLE-002 candidate roster at REDUCED confidence (PENDING AAVE-vs-ETH pair check); basin-lottery vigilance triggers (per-seed spread, Jaccard, Spearman ρ) determine whether multi-seed CONFIRMATION is required before BUNDLE-002 inclusion. |
| **NEGATIVE** | **IS Sharpe < +0.20** OR IS trades < 50 | SPECIALIST-NEGATIVE | AAVE DROPPED from candidate roster after ONE EXPLORATION attempt (per /066 LINK + /067 LTC one-attempt-and-eliminate precedent); mining axis pivots to rank-3 candidate (non-DeFi narrative cluster). The trade-count floor (50 IS trades) per `feedback_v1_trade_rate_floor_50_per_specialist.md` overrides the Sharpe band — if /076 produces <50 IS trades, verdict is NEGATIVE regardless of Sharpe magnitude. |

**Per `feedback_v1_trade_rate_floor_50_per_specialist.md`** (single-symbol specialist OOS floor TIGHTENED to ≥50 OOS per specialist): the analogous IS-side floor is also ≥50 — if /076 IS produces <50 trades, the Sharpe estimate is too noisy (σ_SR ≈ 0.20 at N=25) to support a PROMISING verdict regardless of point estimate. The trade-count floor is a HARD gate.

**Per `feedback_sharpe_floor.md`**: the v1 IS Sharpe > 1.0 floor is the absolute merge gate; merge happens only at BUNDLE-002 assembly time. /076 EXPLORATION verdict gates on the F-AXIS #1 band above (PROMISING-CLEAN ≥ +0.50, PROMISING-TENTATIVE +0.20-+0.50, NEGATIVE <+0.20 or <50 trades), NOT on absolute Sharpe > 1.0.

### F-AXIS #2 — Cross-seed dispersion σ_pop (basin-lottery audit; LOAD-BEARING per /063 family)

The 50-seed inner-ensemble average is the load-bearing SPECIALIST architecture. σ_pop is the cross-seed standard deviation of per-seed IS Sharpe.

| Observed σ_pop | Interpretation |
|---|---|
| σ_pop ≤ 0.20 | METHODOLOGY-VALIDATED-STRONG (mechanism intact; on-par with /063 /064 /065) |
| 0.20 < σ_pop ≤ 0.30 | METHODOLOGY-VALIDATED (LM modal band; on-par with /063 family) |
| 0.30 < σ_pop ≤ 0.40 | METHODOLOGY-PARTIAL (basin-lottery vigilance triggers; flag for Phase 7.4 diagnostic) |
| σ_pop > 0.40 | METHODOLOGY-NEGATIVE (basin-lottery confirmed at 50-seed budget — extreme outcome; flag full LM Master Phase 7.4 falsification audit) |

Additionally per `feedback_v1_basin_lottery_vigilance.md`:
- **per-seed spread > 0.50** OR **Jaccard < 0.40** OR **Spearman ρ < 0.50** triggers verdict downgrade + multi-seed re-validation mandate even if F-AXIS #1 is PROMISING.

### F-AXIS #3 — OOS Sharpe (informational; NOT a verdict gate)

/076 has no prior AAVE OOS reference. LM Master predicts OOS Sharpe modal **−0.10** (90% band [−0.40, +0.30]) — significantly NEGATIVE-skewed due to the bull-IS / bear-OOS regime inversion.

| Band | OOS Sharpe range | Comment |
|---|---|---|
| Preserved/strong | ≥ +0.20 | OOS edge confirms IS not regime-coincident; AAVE bundle-candidate strengthened — but this is an OUTLIER outcome given regime inversion |
| Acceptable | −0.10 to +0.20 | LM Master modal band; consistent with regime inversion + R3 OOD defense |
| Modal-collapse | −0.40 to −0.10 | Consistent with long-bias memorization → bear OOS punishment; **does NOT auto-block /076 PROMISING IS verdict** (IS is the primary gate for /076 EXPLORATION; OOS collapse becomes a BUNDLE-002 blocker, not a /076 EXPLORATION blocker) |
| Catastrophic | < −0.40 | Flag full LM Master Phase 7.4 long-bias diagnostic; per LM Risk Flag 2 explicit catastrophic path |
| Suspicious OOS-dominant lift | ≥ +0.40 with IS Δ vs LM modal +0.20 < +0.10 | Flag possible regime-specific OOS lift (sister to v3 PROMISING-MECHANICAL); needs Phase 7.4 LM Master diagnostic |

OOS Sharpe is **NEVER** the strike adjudicator for /076 (per `feedback_no_cheating.md`). The IS verdict is the strike adjudicator at EXPLORATION budget.

### F-AXIS-FALSIFIER #1 — Per-direction Sharpe + WR + trade count (HARD per LM Master closing note + bull-IS/bear-OOS regime inversion)

The /076 verdict cannot be cleanly interpreted without per-direction reporting given the +13×-cumulative IS bull regime + bear-OOS regime inversion.

The QR Phase 7 evaluation MUST produce a per-direction table:

| Direction | n_trades | win_rate | per-direction Sharpe |
|---|---:|---:|---:|
| LONG | TBD | TBD | TBD |
| SHORT | TBD | TBD | TBD |

| Observed | Verdict modifier |
|---|---|
| balanced (40-60% long trades; per-direction Sharpe within 1σ of each other) | CLEAN — interpret F-AXIS #1 verdict at face value |
| **long-bias mirage** (>70% long trades AND long Sharpe > short Sharpe + 1.5σ) | **DOWNGRADE to NEGATIVE-LONG-BIAS-MIRAGE** regardless of headline IS Sharpe |
| short-bias mirage (>70% short trades AND short Sharpe > long Sharpe + 1.5σ) | DOWNGRADE to NEGATIVE-SHORT-BIAS-MIRAGE regardless of headline IS Sharpe |

The modal failure-mode prediction for /076 (per LM Master + Section 2.8) is **long-bias mirage**. This is the inverse of /075 ATOM's short-bias mirage risk.

### F-AXIS-FALSIFIER #2 — AAVE/ETH prediction correlation (HARD per LM Master Risk Flag 1 + Saturation Risk 2)

The /076 verdict cannot be cleanly evaluated for BUNDLE-002 inclusion without measuring how much of AAVE's specialist signal is ETH-leakage.

The QR Phase 7.4 evaluation MUST produce:
- `rolling_90_corr(AAVE_pred, ETH_pred)` time series across IS + OOS
- mean / median / p90 of the rolling correlation
- the AAVE-specialist feature importance distribution (in particular, the rank of `eth_*` cross-asset features vs within-symbol features)

| Observed | Verdict modifier |
|---|---|
| corr(AAVE_pred, ETH_pred) median < 0.40 + `eth_*` family rank 8-14 (NOT top-3) | CONFIRMS idiosyncratic specialization; AAVE adds residual signal beyond ETH co-movement |
| corr(AAVE_pred, ETH_pred) median 0.40-0.50 + `eth_*` family rank 4-7 | MARGINAL — AAVE's specialist edge partially overlaps ETH/064; flag for BUNDLE-002 pair-check |
| **corr(AAVE_pred, ETH_pred) median ≥ 0.50 OR `eth_*` family rank top-3** | **BUNDLE-002 REJECT CANDIDATE for AAVE+ETH pairing** — AAVE specialist may pass /076 F-AXIS #1 but FAIL BUNDLE-002 pair-check. New verdict: `SPECIALIST-PROMISING-but-BUNDLE-CONTESTED`. Pre-registered new band that the BUNDLE-001 framework has not had to express. |

### F-AXIS-FALSIFIER #3 — Feature importance signature at 0.63 BTC corr / 0.75 ETH corr (PER LM RISK FLAG 1 + 3)

Expected feature-importance signature for AAVE (low BTC corr + HIGH ETH corr):
- Within-symbol primitives (`regime_momentum_signed_5d`, `vwap_dev_*`, `mr_bb_pctb_*`, `atr_pct_*`, `mom_rsi_*`) rank top-5.
- ETH cross-asset features (`eth_ret_*`, `eth_rv_50`, `eth_vs_sym_*`) rank 4-10 (NOT top-3 ideally — top-3 would trigger FALSIFIER #2 reject).
- BTC cross-asset features (`btc_ret_*`, `btc_rv_50`, `btc_funding_*`) rank 8-14.
- ALL-NaN-IS features (`dot_vs_btc_ret_ratio_30`, `eth_vs_btc_ret_ratio_30`) rank effectively zero (LightGBM NaN-handle).

| Observed | Verdict modifier |
|---|---|
| within-symbol dominant top-5; ETH cross-asset rank 4-10 | CONFIRMS partial idiosyncratic specialization; consistent with mechanism rational |
| ETH cross-asset dominant top-3 (`eth_*` family) | **FALSIFIER #2 TRIGGER** — see above |
| BTC cross-asset dominant top-3 (`btc_*` family) | UNEXPECTED — LightGBM found BTC edge despite 0.63 corr; flag for Phase 7.4 mechanism review |
| flat ranking (no clear top-5 dominant) | suggests 50-seed averaging dispersed the signal across many weak features; F-AXIS #2 σ_pop should be elevated |

### F-AXIS-BEHAVIORAL — IS trade count + walk-forward cell coverage

LM Master Phase 4.5 predicts ~100-200 IS trades over 2160 candles (typical SPECIALIST trade rate ~5-10% bar-utilization). Trade-count floor: ≥50 IS trades per `feedback_v1_trade_rate_floor_50_per_specialist.md`.

| Observed | Interpretation |
|---|---|
| IS trades ≥ 100 | sufficient signal-to-noise for cross-seed Sharpe stability |
| 50 ≤ IS trades < 100 | borderline; F-AXIS #1 verdict applies but with reduced confidence; multi-seed validation recommended for any PROMISING tag |
| IS trades < 50 | **AUTO-NEGATIVE** per `feedback_v1_trade_rate_floor_50_per_specialist.md` — Sharpe estimate is too noisy to interpret regardless of point value |

OOS trade count: per LM Master Saturation Risk path, R3 OOD cutoff=0.70 is expected to fire heavily on OOS bear-regime trades (out-of-IS-distribution); OOS trade count may approach the 50-trade floor. Flag at Phase 7 evaluation; if OOS trades < 50, the OOS Sharpe is informational only (NOT a verdict modifier at /076 EXPLORATION budget).

### F-AXIS-COUNTERFACTUAL — N/A for /076 (no anchor to compare against)

/076 is a NEW SYMBOL with no prior AAVE specialist anchor. The counterfactual audit table is N/A. The /065 BTC SPECIALIST + /075 ATOM SPECIALIST `specialist_dispersion.csv` persistence pattern is still required (Section 5.3 item 14).

---

## Section 5 — Risk Mitigation

### 5.1 Axis-specific risk

- **Pre-registered band rigor (HIGH)**: Section 4 F-AXIS bands are frozen at this brief's commit (Section 12). If the QR (or any future post-hoc analyst) re-fits the bands after seeing /076 results, the verdict collapses to METHODOLOGY-FALSIFIED. Phase 8 diary MUST explicitly reference the brief commit SHA when adjudicating.
- **Single-bit discipline (HARD)**: the brief HARDWIRES the locked methodology constants. Only the universe identity deviates vs /075 (and ATR cell + Model A wrapper align with /075). If the runner touches a second axis (e.g., "while we're here, let's try n_trials=50"), the iteration becomes a 2-bit cross-axis confound and the verdict is uninterpretable.
- **Engine parity (HIGH at BUNDLE-002 assembly; LOW at /076 EXPLORATION)**: per `feedback_v1_backtest_live_parity_hard.md` (Critic Check 15), NEW SYMBOL universe extension requires `engine.py:_initial_setup` to add AAVEUSDT to the kline-fetch list when AAVE merges into BUNDLE-002. For /076 EXPLORATION, the backtest runner is the validation surface only. The Critic Check 15 = `BUNDLE-PARITY-VIOLATION` is **N/A at /076 EXPLORATION**.
- **NEGATIVE-pooled-baseline gate UNIQUE PASS (PROMISING signal)**: AAVE TS-mom (5,1) IS Sharpe −0.080 — ONLY eligible NEW SYMBOL passing this gate cleanly. DOT/063 precedent shape. **Action**: Phase 7.4 post-mortem MUST report SPECIALIST IS Sharpe vs trivial-baseline IS Sharpe at (5,1), (5,3), (10,1), (20,5) cells. If SPECIALIST IS Sharpe < trivial-baseline IS Sharpe at any cell where trivial-baseline > +0.50, that is the LINK/LTC-precedent verdict pattern.
- **Bull-IS / bear-OOS regime inversion → long-bias memorization (HIGH)**: 2023+2024+2025-Q1 cumulative IS return ≈ +13× compounded; OOS is bear. Labels likely skew toward direction=+1 hits. Mitigations: 50-seed averaging dampens single-seed bull-fit basins (only partial — consistent bull bias not averaged out); R3 OOD provides regime-defense; Phase 7 evaluation MUST report per-direction Sharpe (F-AXIS-FALSIFIER #1).
- **ETH return correlation 0.75 IS / 0.80 OOS — DeFi-cycle leakage to ETH/064 (HIGH)**: table_05 confirms 0.745 / 0.778 / 0.847 (mean/median/p75 of rolling-90); 0.750 full-IS. Mitigations: F-AXIS-FALSIFIER #2 hardwires rolling-90day corr(AAVE_pred, ETH_pred) reporting at Phase 7.4 + BUNDLE-002 mandate for AAVE-vs-ETH pair check.
- **2 ALL-NaN-IS cross-symbol features (LOW)**: `dot_vs_btc_ret_ratio_30` and `eth_vs_btc_ret_ratio_30` SYMBOL-conditional. LightGBM NaN-handle. Cost: 4.2% colsample slots. Adjustment ≈ −0.04. Logged as future refactor; NOT a /076 blocker.
- **`long_short_zscore_30` and `oi_delta_30_z90` ~34-43% NaN in IS (LOW)**: AAVE-specific long/short and OI data starts mid-2024. LightGBM NaN-handle. Adjustment ≈ −0.02. NOT a /076 blocker.

### 5.2 Risk wrappers (Model A pattern — matches /064 /065 /075)

| Wrapper | /076 setting | Rationale |
|---|---|---|
| R1 (consecutive-SL cool-down) | **DISABLED** | Model A pattern (matches /064 /065 /075); R1 CATALOG-CLOSED for SPECIALIST_mode per `f81cafc3`. Late-streak trades have better edge for Model A symbols per BASELINE_V1 evidence. |
| R2 (DD scaling) | **DISABLED** | Model A pattern (matches /064 /065 /075); R2 is Model E DOT-only. |
| R3 (OOD Mahalanobis cutoff=0.70, 16 SI features SHARED) | **ENABLED** | Active for all v1 SPECIALISTs since /063; applied at AGGREGATOR level (NOT per-seed). Provides regime-defense against OOS shifts — load-bearing for AAVE given bear-OOS expected. |
| R5 (per-coin vol target, 45-day rolling) | **ENABLED** | vt_target_vol=0.3, vt_lookback_days=45, vt_min_scale=0.33, vt_max_scale=2.0. Matches /063 /064 /065 /075. |
| AXIS-R (/074 Mid-Bull SHORT VETO post-aggregator) | **DISABLED** | Mechanism-INVERSE for AAVE: AAVE IS is bull-dominant + bear-tail; the mid-bull SHORT VETO would VETO shorts in mid-bull which is the wrong direction. The /074 rule does NOT apply. |

### 5.3 QE Phase 6.0 Critic pre-flight check items

1. `run_iteration_076.py` is a clone of `run_iteration_075.py` with the SINGLE-BIT change per Section 3.1 (a)-(d): symbols=("AAVEUSDT",), ITERATION_LABEL="v1-076". ATR/wrapper/methodology constants byte-identical to /075.
2. `run_baseline_v1.py` dispatch branch `elif iteration_label == "v1-076" and set(symbols) == set(V1_ITER076_UNIVERSE)` is byte-identical to `v1-075` ATOM branch except for `BacktestConfig(symbols=("AAVEUSDT",))` + model-name string `Model_A_AAVE_specialist_076`.
3. `feature_columns=list(V1_FEATURE_COLUMNS_PRUNED)` (48 cols) is passed explicitly to `LightGbmStrategy` per `feedback_explicit_feature_columns.md`.
4. `FEATURES_BASE_HASH_48COL = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)` is pinned at runner entry and asserts equality with `b81176f893826500536ec5cee8ad00e74bf7edb834290e62e835213defe74ca3` (UNCHANGED 48-col hash).
5. **Parquets NOT regenerated** — `data/features/AAVEUSDT_8h_features.parquet` exists with all 48 cols (table_09); AAVE klines csv is on disk (6178 rows, 2020-10-16 → 2026-06-06).
6. Risk wrappers Model A pattern: `r1_enabled=False, r2_enabled=False, r3_enabled=True, r3_cutoff=0.70, r5_vol_target_enabled=True, r5_vol_target_pct=4.0 (target_vol=0.3 equivalent)`.
7. ATR barriers: TP=2.9, SL=1.45 (ETH/064 cell).
8. `specialist_mode=True`, inner_seeds=50, n_trials=30, outer seed=42 — all unchanged from /063 family.
9. `ENSEMBLE_SIZE=1`, max_depth=5 FIXED, num_leaves=31 FIXED, n_estimators ≤ 500, n_startup_trials=10, mean-of-signed-weights aggregator — all unchanged.
10. Walk-forward embargo applied (`train_end_ms = test_start_ms - embargo_ms`).
11. **NaN handling pre-flight**: assert `df[V1_FEATURE_COLUMNS_PRUNED].dropna(how='all').shape[0] >= 5000` (catastrophic feature-coverage break sanity); confirm `dot_vs_btc_ret_ratio_30` and `eth_vs_btc_ret_ratio_30` are ALL-NaN-by-design (Section 2.9); LightGBM `use_missing=True` (default).
12. `V1_ITER076_UNIVERSE: tuple[str, ...] = ("AAVEUSDT",)` is added to `features_v1/__init__.py` with parallel docstring to V1_ITER075_UNIVERSE.
13. `reports-v1/iteration_v1-076/` directory committed at Phase 8 closeout per HARD rule `0a19e068`.
14. **`specialist_dispersion.csv` persisted** for both IS and OOS windows per LM 7.4 load-bearing patch `153664ed` (continuation of /065 + /075 mandate).
15. Pre-registered F-AXIS bands frozen at brief commit SHA (Section 12); no post-Phase-7 re-tuning permitted.

### 5.4 Historical effect simulation — N/A for NEW SYMBOL

There is no prior AAVE specialist roster to simulate against. The expected behavior is given by the BUNDLE-001 member IS Sharpe distribution (mean +0.16, std ≈ 0.30) adjusted by the LM Master Phase 4.5 mechanism analysis (Section 2 H1a-H1f). The LM Master modal +0.20 minus the table_09 NaN-tax (−0.04) gives QR-modal-adjusted **+0.16 IS** (PROMISING-TENTATIVE band low end).

---

## Section 6 — Phase 5.5 Gate Pre-Flight (load-bearing for QE)

Phase 5.5 gate items (must clear ALL before QE Phase 6 fires):

| # | Check | Verifier | Status @ brief authoring |
|---|---|---|---|
| G1 | EDA script `analysis/v1-076/eda.py` committed and tables 01-10 persisted | `git log` shows commit; `analysis/v1-076/table_*.csv` exist | TO BE COMMITTED in Phase 5 closeout |
| G2 | IS firewall: every loaded path asserts no `out_of_sample` substring | `_assert_is_only_path` helper present in `eda.py`; `is_only(df)` filter applied | PRESENT |
| G3 | Brief Section 0.6 axis-family declaration and rotation status | This brief Section 0.6 | DONE |
| G4 | Brief Section 2.5 HIGH-RISK declaration | This brief Section 2.5 | DONE |
| G5 | Brief Section 3.4 explicit LM Master response | This brief Section 3.4 | DONE |
| G6 | Brief Section 4 F-AXIS bands pre-registered (frozen at commit SHA) | This brief Section 4 | DONE |
| G7 | Brief Section 5 Risk Mitigation with IS-calibrated thresholds | This brief Section 5 | DONE |
| G8 | Brief Section 11 backtest-live parity statement | This brief Section 11 | DONE |
| G9 | `V1_ITER076_UNIVERSE` declared in features_v1 | `grep V1_ITER076_UNIVERSE src/crypto_trade/features_v1/__init__.py` | TO BE ADDED in Phase 6 setup |
| G10 | `run_iteration_076.py` clone with single-bit change | `git log` shows new runner | TO BE ADDED in Phase 6 setup |
| G11 | Dispatch branch `elif iteration_label == "v1-076"` in run_baseline_v1.py | `grep "v1-076" run_baseline_v1.py` | TO BE ADDED in Phase 6 setup |
| G12 | Features parquet exists with 48 cols populated | table_09 audit | DONE (data/features/AAVEUSDT_8h_features.parquet) |
| G13 | 2 ALL-NaN-IS cross-symbol features documented as LightGBM-NaN-handled | This brief Section 2.9 + 5.1 | DONE |
| G14 | `_assert_is_only_path` test on EDA: `pytest analysis/v1-076/test_eda_firewall.py` (optional) | If a pytest suite for EDA firewall is added | OPTIONAL — not required at G-level |

Phase 5.5 gate verdict at brief authoring: **READY FOR PHASE 6 SETUP** (G9-G11 are Phase 6 setup-side tasks; the QR brief is complete).

---

## Section 7 — Falsification Conditions (HARD anti-tuning)

Per `feedback_no_cheating.md`, the following must hold for /076 verdict integrity:

1. **F-AXIS #1 bands** (Section 4) frozen at brief commit SHA. No post-Phase-7 re-tuning. If observed IS Sharpe is +0.19, the verdict is NEGATIVE (NOT "let's call it PROMISING-TENTATIVE-MARGINAL").
2. **Trade-count floor 50 IS** (per `feedback_v1_trade_rate_floor_50_per_specialist.md`) — AUTO-NEGATIVE if IS trades < 50.
3. **Per-direction Sharpe falsifier** (F-AXIS-FALSIFIER #1) — long-bias mirage downgrades headline PROMISING to NEGATIVE-LONG-BIAS-MIRAGE.
4. **AAVE/ETH pred-correlation falsifier** (F-AXIS-FALSIFIER #2) — corr ≥ 0.50 or `eth_*` family top-3 downgrades to SPECIALIST-PROMISING-but-BUNDLE-CONTESTED.
5. **No methodology constant change post-brief**. If the QE detects a mismatch and proposes "let's bump n_trials to 50 for AAVE specifically", that is a methodology-violation; ABORT and re-evaluate.
6. **No EDA re-run with different IS-window definition** (`feedback_no_cheating.md`).
7. **No retroactive band-edge tuning to make the verdict land in a chosen band** — bands frozen at brief commit; verdict is mechanical.

---

## Section 8 — Expected Outputs / Reports

| Artifact | Path | Required-by |
|---|---|---|
| EDA script | `analysis/v1-076/eda.py` | Phase 5.5 G1 |
| EDA tables | `analysis/v1-076/table_*.csv` (10 tables) | Phase 5.5 G1 + Section 2 evidence |
| Brief | `briefs-v1/iteration_v1-076/research_brief.md` | Phase 5 closeout |
| LM Master advisor | `briefs-v1/iteration_v1-076/lgbm_advisor.md` | Phase 4.5 (already present) |
| Critic pre-flight | `briefs-v1/iteration_v1-076/critic_preflight.md` | Phase 6.0 |
| Phase 5.5 gate review | `briefs-v1/iteration_v1-076/phase5p5_gate.md` | Phase 5.5 |
| Runner | `run_iteration_076.py` | Phase 6 setup |
| Dispatch branch | `run_baseline_v1.py` (elif `v1-076`) | Phase 6 setup |
| Universe constant | `src/crypto_trade/features_v1/__init__.py` (V1_ITER076_UNIVERSE) | Phase 6 setup |
| Backtest reports | `reports-v1/iteration_v1-076/{in_sample,out_of_sample}/` + `comparison.csv` + `per_seed_sharpe.csv` + `optuna_best_params.csv` + `specialist_dispersion.csv` | Phase 7 closeout |
| Diary | `diary-v1/iteration_v1-076.md` | Phase 8 closeout |

---

## Section 9 — Cycle-7 Roster Position

Per `feedback_v1_cycle6_per_symbol_regime_specialist_mandate.md`, cycle-7 mining strategy:
- BUNDLE-001 (DOT/063 + ETH/064 + BTC/065) is the running BUNDLE roster.
- /066 LINK, /067 LTC: ELIMINATED (positive-baseline trap).
- /068-/070, /072, /073: BUNDLE-001-improvement axes — 3 CLOSED FAIL.
- /074 ETH-IMPROVED-V3: active, verdict pending.
- /075 ATOMUSDT NEW SYMBOL: active, verdict pending — first universe-extension mining attempt.
- **/076 AAVEUSDT NEW SYMBOL**: this iteration — second universe-extension mining attempt, first DeFi-lending narrative candidate.

If /076 PROMISING (any band), AAVE joins the BUNDLE-002 candidate roster PENDING the AAVE-vs-ETH pair check (F-AXIS-FALSIFIER #2). CONFIRMATION assembles regime-complementary specialists from the running roster (per the per-symbol regime-specialist mandate, IS-regime-diverse bundles are hypothesized to generalize OOS).

If /076 NEGATIVE, mining axis pivots to rank-3 candidate. **Pre-registered narrative-rotation mandate** per LM Saturation Risk 1: /077+ must rotate to non-DeFi narrative cluster (storage / interoperability / payments / L2). DeFi-lending narrative consumed by /076 attempt.

The autopilot mining pipeline continues regardless of /076 outcome — per user directive 2026-06-06.

---

## Section 10 — Trade-rate floor compliance

Per `feedback_v1_trade_rate_floor_50_per_specialist.md` (single-symbol specialist OOS floor TIGHTENED to ≥50 OOS per specialist):
- **IS floor**: ≥50 IS trades required for any PROMISING tag (Section 4 F-AXIS #1 NEGATIVE auto-fires at <50 IS trades).
- **OOS floor**: ≥50 OOS trades required for BUNDLE-002 inclusion at CONFIRMATION (NOT a /076 EXPLORATION gate — /076 is single-outer-seed EXPLORATION; OOS trade count is informational at this stage but elevated risk per LM Saturation Risk 4 R3 OOD over-firing in bear-OOS).
- **30-49 trades fallback**: 7-outer-seed validation OR baseline anchor fallback per the rule. NEW SYMBOL has no baseline anchor → 7-outer-seed validation is the only fallback (mandates a follow-up multi-seed iteration if /076 lands 30-49 trades).
- **<30 trades**: auto-reject (NEGATIVE verdict).

This brief inherits the rule. Phase 7 evaluation reports IS+OOS trade counts explicitly.

---

## Section 11 — Backtest-Live Parity Statement

Per `feedback_v1_backtest_live_parity_hard.md` (Critic Check 15 = `BUNDLE-PARITY-VIOLATION`):

- **At /076 EXPLORATION**: parity is N/A. /076 is a single-coin SPECIALIST EXPLORATION; no BUNDLE assembly. The backtest runner is the validation surface. No `engine.py:_tick` change is required at /076.
- **At BUNDLE-002 assembly time (if /076 PROMISING AND F-AXIS-FALSIFIER #2 not triggered)**: AAVE SPECIALIST inclusion in BUNDLE-002 requires:
  - `engine.py:_initial_setup` to add `AAVEUSDT` to the kline-fetch list (8h interval; matches v1 BUNDLE-001 fetch pattern).
  - The BUNDLE-002 dispatch (when assembled in a future iteration) must wire the AAVE SPECIALIST's `LightGbmStrategy` instance into the per-symbol model registry in `engine.py`, byte-identical to the backtest-side instance (same `feature_columns`, same R3/R5 wrappers, same ATR cell, same threshold).
  - **No coin overlap rule** (`feedback_v1_bundle_no_coin_overlap.md`): AAVE owned by exactly ONE component (the AAVE SPECIALIST); DOT remains owned by the DOT SPECIALIST; ETH by ETH; BTC by BTC. No cross-symbol pooling.
  - **Bundle weights IS-only** (`feedback_v1_bundle_weight_is_only.md`): if BUNDLE-002 introduces a per-symbol weight calibration, the weights must be derived from `analysis/iteration_v1-NNN/weight_calibration.py` reading ONLY IS data.
  - **AAVE-vs-ETH pair check (HARD)**: per F-AXIS-FALSIFIER #2 + LM Saturation Risk 2, if rolling-90day corr(AAVE_pred, ETH_pred) ≥ 0.50 OR `eth_*` family top-3 importance, BUNDLE-002 must use AAVE OR ETH, not both. Pre-registered.
- **No post-trade aggregation/netting**: the BUNDLE dispatch is per-symbol additive — no netting across symbols.

This brief pre-commits to the parity surface at BUNDLE-002 assembly time. /076 EXPLORATION runs only the backtest-side validation; no engine code is touched.

---

## Section 12 — Pre-Registration Commit SHA (HARD anti-tuning anchor)

The F-AXIS bands in Section 4, the falsification conditions in Section 7, and the pre-registered methodology constants in Section 3.2 are FROZEN at the commit SHA of this brief.

**Brief commit SHA**: TO BE FILLED in Phase 5 closeout (the QR commits this brief with message `docs(iter-v1/076): Phase 1-5 QR — AAVE NEW SYMBOL specialist EDA + brief`; the resulting SHA is the freeze anchor).

Any post-Phase-7 re-fitting of bands, retroactive band-edge adjustment, or methodology constant change relative to this brief's content collapses the /076 verdict to **METHODOLOGY-FALSIFIED** and forfeits the iteration regardless of the headline IS Sharpe.

---

## Section 13 — Summary

AAVEUSDT is the second NEW SYMBOL universe-extension SPECIALIST EXPLORATION in v1 history (after /075 ATOM), the first DeFi-lending narrative specialist candidate, and the ONLY eligible NEW SYMBOL passing the NEGATIVE-pooled-baseline gate cleanly (TS-mom (5,1) IS Sharpe −0.080; table_06) — the structural DOT/063 precedent shape that was the necessary precondition for specialist edge extraction. The mechanism-rational case is: NEGATIVE-baseline gate UNIQUE PASS + ETH-class mid-vol regime (table_02 IS-weighted ~95% annualized) matches the (2.9, 1.45) ATR cell + chop-dominant 54% IS regime (table_04) with all 3 regimes represented + 48-col `V1_FEATURE_COLUMNS_PRUNED` has 46 clean features for AAVE (2 ALL-NaN-IS by SYMBOL-conditioning, LightGBM NaN-handle; funding cols populate cleanly — LM Risk Flag 5 REFUTED).

The risks are: **(1) ETH return correlation 0.75 IS / 0.80 OOS (table_05)** — DeFi-cycle leakage to ETH/064 — HARDWIRED as F-AXIS-FALSIFIER #2 + BUNDLE-002 pair-check mandate; **(2) bull-IS / bear-OOS regime inversion** — IS cumulative return ≈ +13× compounded (table_08), OOS bear — long-bias memorization → modal OOS collapse path — HARDWIRED as F-AXIS-FALSIFIER #1; (3) basin-lottery vigilance at single-outer-seed=42 EXPLORATION budget (mitigated by 50-INNER-seed averaging but not eliminated).

Modal predicted IS Sharpe **+0.20** (LM Master Phase 4.5; QR-adjusted +0.16 after NaN-tax). PROMISING-CLEAN at +0.50; PROMISING-TENTATIVE at +0.20-+0.50; NEGATIVE at <+0.20 or <50 trades. Modal predicted OOS Sharpe **−0.10** (LM Master). Verdict adjudication is mechanical against Section 4 frozen bands.

Single-bit deviation vs /075 dispatch: `SYMBOLS=("AAVEUSDT",)`, `ITERATION_LABEL="v1-076"`. ATR cell + wrapper + all other methodology constants byte-identical to /075 (and to the /064 /065 Model A family). All other methodology constants HELD per user directive 2026-06-06.

NEW SYMBOL strike rule: one-attempt-and-eliminate per /066 LINK + /067 LTC precedent. Narrative-rotation mandate: /077+ must rotate to non-DeFi cluster.
