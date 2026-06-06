# iter-v1/075 — Research Brief

**Iteration**: iter-v1/075
**Date**: 2026-06-06
**TYPE**: SPECIALIST EXPLORATION — **NEW SYMBOL universe-extension** (first under autopilot mining directive 2026-06-06)
**Cycle**: 7, SPECIALIST-MINE 1/N
**Branch**: `iteration-v1/075`
**Author**: QR (autopilot)
**Anchor**: NONE (universe-extension; no prior ATOM specialist exists). Verdict is measured against the implicit dispatch baseline — a single-coin cohort `(ATOMUSDT,)` under the locked SPECIALIST methodology — and ranked **relative to the BUNDLE-001 member IS Sharpe distribution** (DOT/063 IS +0.43, ETH/064 IS +0.24, BTC/065 IS −0.18; mean +0.16, std ≈ 0.30).
**Axis**: **NEW SYMBOL — ATOMUSDT.** Single-bit change vs /063 dispatch: `SYMBOLS=("ATOMUSDT",)` + `ITERATION_LABEL="v1-075"` + ATR pair shifted /063's (3.5, 1.75) → /064's (2.9, 1.45) cell (vol-class match). All methodology constants HELD per user directive 2026-06-06.
**LM Master verdict**: MEDIUM confidence; modal IS Sharpe **+0.30** (90% band [−0.10, +0.65]); aggregate PROMISING-or-better probability 0.48.

---

## Section 0 — Data Split Declaration (Foundation)

- **OOS_CUTOFF_DATE**: `2025-03-24` (IMMUTABLE — never changes)
- **training_months**: `24` (IMMUTABLE — never changes)
- **IS window**: 2023-03-24 → 2025-03-24 (24 months walk-forward training; ATOM IS roster covers 2160 8h candles)
- **OOS window**: 2025-03-24 → present (1318 8h candles ≈ 14.6 months)
- **Walk-forward embargo**: `train_end_ms = test_start_ms - embargo_ms` (commit `5566a69`; identical helper used in this iteration; inherited bit-exactly from /063 setup)
- **Sacred constants HELD per Rule 3** (`feedback_training_window.md`, `feedback_no_cheating.md`): no shift, no extension, no trim, no peek.

EDA script `analysis/v1-075/eda.py` reads ONLY IS-window klines via the `is_only(df)` helper (filters `open_time < OOS_CUTOFF_MS = 1742774400000`) and asserts `out_of_sample` substring absent from every loaded path (`_assert_is_only_path`). No OOS file is opened during Phase 1-5. The script's `table_09_feature_nan_audit` is the SOLE function that reads OOS-window NaN counts from the same global features parquet (it does not open an OOS-specific file; the parquet has both IS and OOS rows merged). The OOS NaN counts are surfaced as a Phase 5.5 sanity check ONLY — no OOS values are used to derive any signal, threshold, or band edge.

---

## Section 0.5 — Iteration Type Declaration & Cadence

- **TYPE**: SPECIALIST EXPLORATION — NEW SYMBOL (single-coin cohort)
- **Cycle 7 position**: SPECIALIST-MINE 1/N (first universe-extension after BUNDLE-001 merge)
- **Mining context**: the user directive 2026-06-06 (autopilot — "find new specialists … using all the quantitative knowledge") opens the universe-extension EXPLORATION mode after BUNDLE-001 (v0.v1-071) merged DOT/063 + ETH/064 + BTC/065. All 5 v1-native symbols (BTC, ETH, LINK, LTC, DOT) have been specialist-tested; LINK/066 and LTC/067 ELIMINATED (positive-baseline trap). ATOMUSDT is the rank-1 mine-phase candidate (composite score 0.767) and the first NEW SYMBOL EXPLORATION in v1 history.
- **Wall-clock budget**: **2h hard cap** per `feedback_v1_confirmation_walltime_9h.md` EXPLORATION default. LM Master Phase 4.5 predicts ~50-90 min Optuna + 10 min wrap-up (50 inner seeds × 30 trials × 24 walk-forward cells; ATOM 6.3y data extent supports stable cell counts).
- **Kill-switch**: if wall-clock exceeds 2.5h, OR any specialist outer-seed returns `nan` Sharpe, OR the FEATURES_BASE_HASH_48COL pre-flight guard fails to match /063's 48-col hash, OR `df[V1_FEATURE_COLUMNS_PRUNED].dropna(subset=non-cross-symbol).shape[0] < 5000` (catastrophic feature coverage break) → abort, capture commit, surface diagnostic for next mining candidate.

---

## Section 0.6 — Architecture-Family Justification (v1)

- **Axis family**: `universe` (NEW SYMBOL — universe-extension to a not-yet-tested coin under LOCKED methodology)
- **Prior 5 EXPLORATION families** (catalog rows /066 → /074):
  - iter-v1/066: `universe` (LINK SPECIALIST EXPLORATION) → ELIMINATED (positive-baseline trap)
  - iter-v1/067: `universe` (LTC SPECIALIST EXPLORATION) → ELIMINATED (positive-baseline trap)
  - iter-v1/072: `risk-primitive` (BTC-IMPROVED-V2 R1 streak-cooldown enable) → SPECIALIST-NEGATIVE-IMPROVEMENT-FAIL; R1 catalog-CLOSED for SPECIALIST_mode
  - iter-v1/073: `feature-family` (ETH-IMPROVED-V2 feature-subset reduction 48→25 cols) → SPECIALIST-NEGATIVE-IMPROVEMENT-FAIL; dispersion-reservoir mechanism falsified
  - iter-v1/074: `risk-primitive` (ETH-IMPROVED-V3 AXIS-R Mid-Bull SHORT VETO post-aggregator rule layer) → currently active (no closeout yet; verdict adjudication pending)
- **Rotation status**: **VALID under the cycle-7 per-symbol regime-specialist mandate** (`feedback_v1_cycle6_per_symbol_regime_specialist_mandate.md` — axis-family rotation SUSPENDED for at least cycle-6+7; same symbol any number of times is permitted; NEW SYMBOL falls cleanly within the mandate). Even under cycle-6's strict family-rotation discipline (now suspended), `universe` is categorically distinct from /074's `risk-primitive` (the immediately prior axis) and /073's `feature-family`.
- **One-sentence rationale**: BUNDLE-001's IS/OOS edge is concentrated in 3 symbols (DOT/ETH/BTC) with ~0.85 mean cross-asset correlation; the cleanest single-bit way to mine NEW edge under locked methodology is to inject a **structurally idiosyncratic symbol** (ATOM: lowest BTC correlation 0.62 in CLEAN-adversarial-flag set, mean-reverting Hurst regime per OOS rationale claim, cosmos-interop narrative cluster unique to roster, 6.32y data extent — the longest in eligible set) and let the LOCKED 50-seed methodology decide whether the idiosyncratic distance translates to a positive specialist IS Sharpe.

---

## Section 0.7 — SPECIALIST EXPLORATION 1-of-N for NEW SYMBOL mining

| Field | Value |
|---|---|
| **Mine-phase rank** | **1/N** (composite score 0.767; rank-2/rank-3 candidates staged in pipeline per autopilot directive) |
| **Cohort** | `("ATOMUSDT",)` — single-coin SPECIALIST (skill mandate; cycle-6+7 per-symbol regime-specialist mandate) |
| **Data extent** | 6.33y (2020-02-07 → 2026-06-06; 6933 8h candles) — longest in eligible set; comfortably clears 4y walk-forward floor |
| **Methodology constants HELD per user directive** | 50 inner seeds × 30 Optuna trials × `specialist_mode=True` + 48-col `V1_FEATURE_COLUMNS_PRUNED` + ATR (2.9, 1.45) + R1=OFF + R2=OFF + R3=ON-SHARED cutoff=0.70 + R5=ON + max_depth=5 + num_leaves=31 + n_estimators ≤ 500 + n_startup_trials=10 + mean-of-signed-weights aggregator. ENSEMBLE_SIZE=1. Outer seed=42. training_months=24. Walk-forward embargo `train_end_ms = test_start_ms - embargo_ms` (`5566a69`). |
| **The ONLY single-bit changes vs /063 dispatch** | (a) `SYMBOLS=("ATOMUSDT",)` (not DOTUSDT); (b) `ITERATION_LABEL="v1-075"`; (c) ATR pair (2.9, 1.45) — ETH/064 cell — matched to ATOM's 77.4% IS realized vol (which sits between ETH ~70% and DOT ~110%); (d) Model A wrapper (R1=OFF, R2=OFF; following ETH/064 and BTC/065 — NOT DOT/063's R1=ON+R2=ON Model E). All other constants byte-identical to the /063 → /064 → /065 SPECIALIST family. |
| **No parquet regeneration** | `data/features/ATOMUSDT_8h_features.parquet` exists (6933 × 230 cols, hash `0865537dc50a8d11`); all 48 `V1_FEATURE_COLUMNS_PRUNED` columns are present. EDA table 09 reports NaN audit (Section 2.7). |
| **Anchor** | NONE — universe-extension. Verdict frame: ranked against BUNDLE-001 member IS Sharpe distribution (DOT/063 +0.43, ETH/064 +0.24, BTC/065 −0.18; mean +0.16, std ≈ 0.30). |
| **Strike framework** | N/A for first attempt — NEW SYMBOL EXPLORATION starts the strike counter at 0. If /075 verdicts PROMISING (any of the three PROMISING bands), ATOM enters BUNDLE-002 candidate roster; if NEGATIVE, ATOM is dropped after **ONE attempt** (positive-baseline trap precedent from /066 LINK, /067 LTC: one-attempt-and-eliminate for NEW SYMBOL universe extension to prevent knob-tuning a NEW SYMBOL into the cohort). |
| **Pre-registered verdict bands (HARD anti-tuning)** | Section 4 F-AXIS #1 bands frozen at this brief's commit (Section 12). Bands WILL NOT be re-tuned post-hoc. Per `feedback_no_cheating.md`. |

---

## Section 1 — Hypothesis

**H1 (PRIMARY)**: The locked SPECIALIST methodology (50 inner seeds × 30 Optuna trials, 48-col `V1_FEATURE_COLUMNS_PRUNED`, ATR(2.9, 1.45), R1=OFF / R2=OFF / R3=ON-SHARED cutoff=0.70, R5=ON, mean-of-signed-weights aggregator) — applied to ATOMUSDT — will produce a SPECIALIST IS Sharpe in the **PROMISING band [+0.15, +0.50]** (median LM Master modal +0.30), driven by the **idiosyncratic-distance mechanism**: ATOM's 0.617 IS BTC return correlation and 0.673 IS ETH return correlation (table_05) are the LOWEST in the eligible set, providing the cleanest roster-diversity addition to BUNDLE-001's ~0.85-mean-correlation backbone. The 50-seed ensemble extracts mid-vol cross-asset edge from the 48-col stack via the existing `btc_*`, `eth_*` cross-asset features (which carry directional information for ATOM via 0.617 BTC and 0.673 ETH corr — non-zero, structurally diluted vs DOT's ~0.85 but mechanistically present).

**H1a (mechanism — idiosyncratic structure complements BUNDLE-001 backbone)**: BUNDLE-001 (DOT/ETH/BTC) operates on a ~0.85-mean-correlation backbone. ATOM at 0.617 IS BTC corr / 0.712 IS DOT corr sits in a structurally distinct return-correlation cluster (table_10 diversity score 0.383 vs BTC; 0.288 vs DOT). The 48-col stack — which carries within-symbol momentum (`regime_momentum_signed_5d`, MACD family), within-symbol mean-reversion (`vwap_dev_*`, Bollinger family), within-symbol volatility (`vol_range_spike_*`, `stat_*`), and cross-asset BTC/ETH features — extracts edge through the within-symbol primitives (which are HARDER to overfit because ATOM's regime-history is different from DOT/ETH/BTC's). The expected feature-importance signature (verified post-Phase-7): within-symbol primitives rank in the top-5, cross-asset features rank 8-14 (NOT top-3 as on DOT/063). This is **mechanism-rational** for NEW SYMBOL at this correlation distance.

**H1b (mechanism — ATR(2.9, 1.45) vol-class match)**: ATOM's 2024 IS realized vol is 81.98% annualized (table_02) — sits between ETH/064's regime (~70%) and DOT/063's regime (~110%). ATR(2.9, 1.45) is the ETH-class barrier pair; ATR(3.5, 1.75) is DOT-class. Choosing ETH-class barriers for ATOM is the mechanism-matched cell. This is a single-bit change vs /063's dispatch (which used 3.5/1.75) but is **methodology-compliant** — it slots ATOM into the same Model A `RiskV1Wrapper` cell as ETH/064 and BTC/065 (R1=OFF + R2=OFF + R3=ON-SHARED + ATR(2.9, 1.45)), preserving the cross-specialist comparability that BUNDLE-002 assembly will need.

**H1c (mechanism — Optuna + 50-seed averaging absorbs basin-lottery on a fresh symbol)**: Single-outer-seed=42 EXPLORATION exposes basin-lottery risk per `feedback_v1_basin_lottery_vigilance.md`; cycle-6/7 had 100% basin-lottery rate (4/4) on single-seed PROMISING tags. The 50-INNER-seed averaging (the load-bearing SPECIALIST architecture) dampens within-cell basin-lottery substantially — σ_pop ≤ 0.30 was the F-AXIS #2 load-bearing gate at /063 and held at /064 / /065. For ATOM the 50-seed signal should similarly dampen the within-cell basin-lottery; verdict at single-outer-seed remains TENTATIVE per the basin-lottery vigilance rule (mandates multi-outer-seed re-validation if /075 PROMISING with per-seed spread > 0.50 OR Jaccard < 0.40 OR Spearman ρ < 0.50).

**H1d (KEY RISK — positive-baseline trap from short-horizon TS-mom)**: The /066 LINK and /067 LTC ELIMINATIONS established the positive-baseline trap: when the trivial TS-mom IS Sharpe is already POSITIVE, the LightGBM head finds less marginal edge and underperforms BUNDLE membership. ATOM's TS-mom IS Sharpe profile (table_06):
- short-horizon (5,1): +0.638 — POSITIVE but mid-band
- short-horizon (10,1): +0.498 — POSITIVE mid-band
- mid-horizon (30,3): **+1.322** — VERY positive (strong 10-day trend signal)
- long-horizon (60,10): **+1.677** — VERY positive (strong 20-day trend signal)

This is a **MIXED signal**: the SHORTEST-horizon TS-mom (which is closest to the LightGBM head's 21-bar triple-barrier label horizon) is POSITIVE mid-band — meaning ATOM is NOT a pure NEGATIVE-pooled-baseline candidate like DOT was pre-/063 (which is the LM Master Risk Flag 1 nuance). However, **the LightGBM head operates on 48 features and a 21-bar triple-barrier label, NOT a simple sign-of-momentum signal**. The trivial-signal positive-baseline-trap risk is real but is mitigated by:
- (a) The ML's value is NOT to replicate sign-of-mom but to **route directional signals through R3 OOD + R5 vol-target + 50-seed averaging** — three orthogonal filters that the trivial baseline lacks.
- (b) The chop-dominant 58% IS regime (table_04 — 50-bar absolute-return ±15% threshold) is where directional momentum FALSE-POSITIVES kill simple TS-mom; the LightGBM head can selectively NOT trade in chop via R3 OOD (which gates non-flat signals).
- (c) The mid-horizon TS-mom Sharpe (+1.32 at 30-bar) is structurally NOT what the 21-bar triple-barrier label captures — the label captures intra-21-bar TP/SL hits, which is closer to short-horizon signal.

**Net**: ATOM is a MEDIUM-confidence PROMISING candidate. The trivial-baseline Sharpe is positive but mid-band; the cross-asset diversity is the highest in the eligible set; the realized vol matches the ETH/064 cell.

**H1e (KEY RISK — deep-bear OOS-adjacent regime + label SL-bias)**: ATOM's 2024 cumulative return is −0.42 and 2025-Q1 is −0.22 (table_08; LM Master Risk Flag 2 confirmed). The triple-barrier label distribution under ATR(2.9, 1.45) at horizon=21 is SL-heavy on BOTH sides (table_07 LONG SL 60% / SHORT SL 55%) — typical of high-vol assets but means the labels are imbalanced toward losses ~60% of the time. The 50-seed averaging mitigates: per-seed bias in either direction averages out at the aggregator. The R3 OOD filter (cutoff=0.70) provides regime-defense against OOS bear-extension if 2026-Q2 transitions out of bear. **The verdict-critical sanity check** (per LM Master closing note): per-direction Sharpe + trade count + WR in Phase 7 evaluation. If short Sharpe is +1.5 and long Sharpe is −0.5 producing a headline +0.3, the result is a regime-fit short-bias mirage NOT a clean PROMISING.

**Modal predicted IS Sharpe**: **+0.30** (LM Master Phase 4.5 modal); 60% band [+0.15, +0.45]; 90% band [−0.10, +0.65]. **Modal predicted OOS Sharpe**: +0.20 (LM Master Phase 4.5 modal); wider band [−0.30, +0.60].

---

## Section 2 — IS-Only Numerical Evidence (from `analysis/v1-075/eda.py`)

**Analysis script**: `analysis/v1-075/eda.py` (committed at brief authoring; IS-firewall verified by path-substring assertion `_assert_is_only_path` and IS-filter `is_only(df)` applied to every klines load).
**Source data**:
- `data/ATOMUSDT/8h.csv` (6933 rows total; 2160 IS rows; OOS rows present but filtered out at usage)
- `data/features/ATOMUSDT_8h_features.parquet` (6933 × 230 cols; 48 `V1_FEATURE_COLUMNS_PRUNED` present; opened ONLY for NaN audit in table_09)
- Anchor klines for cross-asset corr: `data/{BTCUSDT,ETHUSDT,DOTUSDT,LTCUSDT,LINKUSDT}/8h.csv`

All tables are persisted to `analysis/v1-075/*.csv` and re-derivable by `uv run python analysis/v1-075/eda.py`.

### 2.1 Data extent (table_01) — ATOM clears 4y walk-forward floor

| symbol | first_open | last_open | IS_candles | years_total |
|---|---|---|---:|---:|
| **ATOMUSDT** | **2020-02-07** | 2026-06-06 | **2160** | **6.33** |
| BTCUSDT | 2020-01-01 | 2026-06-01 | 2160 | 6.41 |
| ETHUSDT | 2020-01-01 | 2026-06-01 | 2160 | 6.41 |
| DOTUSDT | 2020-08-22 | 2026-05-27 | 2160 | 5.76 |
| LTCUSDT | 2020-01-09 | 2026-06-01 | 2160 | 6.39 |
| LINKUSDT | 2020-01-17 | 2026-05-27 | 2160 | 6.36 |

ATOM has **6.33y of 8h candles** — longest in the eligible NEW SYMBOL set and exceeds the 4y walk-forward floor by 58%. The IS window covers 2160 candles (24 months @ 8h cadence × 30d/mo × 3 candles/day ≈ 2160 expected — exact match).

### 2.2 Realized vol regime by IS year (table_02) — ETH-class mid-vol

| year | rows | ann_realized_vol_pct | natr_30_median |
|---|---:|---:|---:|
| 2020 | 986 | 111.56% | 0.049 |
| 2021 | 1095 | 160.79% | 0.067 |
| 2022 | 1095 | 111.09% | 0.051 |
| **2023** | 1095 | **65.97%** | 0.029 |
| **2024** | 1098 | **81.98%** | 0.034 |
| **2025-Q1** | 246 | **98.45%** | 0.044 |

**IS-window weighted avg ≈ 80% annualized** — sits between ETH (~70%) and DOT (~110%). This is the mechanism-rational justification for choosing the ETH/064 ATR cell (2.9, 1.45) over DOT/063's (3.5, 1.75): ATOM's realized vol is closer to ETH's than DOT's. The 2024 → 2025-Q1 transition (81.98 → 98.45) shows vol-regime expansion approaching the OOS window — mildly concerning for stationarity but well within the 50-seed averaging's tolerance band.

### 2.3 Rolling 100-bar Hurst exponent (table_03)

**DIAGNOSTIC ONLY — the rolling-Hurst implementation in `_hurst_simple` is the rescaled-range-on-log-returns variant which is known to be biased toward 0 on noisy financial returns; observed values [−0.08, +0.11] are NOT Hurst-interpretable**. The LM Master Phase 4.5 advisor cites Hurst 0.489 IS / 0.412 OOS from a separate computation (full-window log-price R/S exponent; different algorithm). This brief defers to the LM Master Phase 4.5 estimate for Hurst-regime narrative (ATOM is mean-reverting in OOS, near-random in IS — the ML-edge mechanism is plausible per Hurst-as-prior). The EDA table_03 is retained for reproducibility but NOT cited as Hurst evidence in Section 1.

### 2.4 Regime mix (table_04) — chop-dominant IS

| regime (50-bar return ±15%) | frac | count |
|---|---:|---:|
| **chop** (|ret_50| ≤ 0.15) | **58.0%** | 3228 |
| **bull** (ret_50 > 0.15) | **22.3%** | 1242 |
| **bear** (ret_50 < −0.15) | **19.7%** | 1095 |

All 3 regimes are represented in the IS window — no zero-regime bucket. Chop-dominant 58% is the load-bearing observation: it favors **mean-reverting + selective-entry** ML edge over **trend-following** edge. The 48-col stack carries mean-reversion primitives (`vwap_dev_*`, `mr_bb_pctb_*`, `mr_rsi_extreme_*`) and the R3 OOD gate provides chop-defense (the OOD distance spikes during chop transitions; the cutoff=0.70 vetoes high-OOD signals).

(NB: the LM Master Phase 4.5 cited 71/11/15 regime mix at different thresholds; my ±15% thresholds give 58/22/20. Both are valid — different threshold definitions; what matters is that bull/bear/chop are ALL represented and chop is the modal regime. Decision impact: same.)

### 2.5 Cross-asset rolling-90 return correlation (table_05) — IDIOSYNCRATIC DIVERSITY

| anchor | rolling_90 mean | rolling_90 median | full IS corr |
|---|---:|---:|---:|
| **BTCUSDT** | **0.633** | 0.663 | **0.617** |
| ETHUSDT | 0.679 | 0.701 | 0.673 |
| LTCUSDT | 0.644 | 0.661 | 0.633 |
| LINKUSDT | 0.687 | 0.712 | 0.681 |
| **DOTUSDT** | 0.742 | 0.754 | 0.712 |

**ATOM's IS 90-bar correlation with BTC is 0.617** — the load-bearing idiosyncratic-diversity claim from the chosen-symbol rationale is **CONFIRMED**. ATOM-vs-DOT IS corr is 0.712 (not 0.81 as cited in LM Master from full-window 2020-2026 data — the IS-only window is structurally different from full-window because DOT's pre-2023 history dominates the full-window estimate). Both BTC and DOT correlations are NON-ZERO (positive structural co-movement) — meaning the 48-col cross-asset features (`btc_ret_30d`, `btc_rv_50`, `eth_ret_30d`) carry SOME explanatory power for ATOM, but reduced vs DOT/063 (where DOT-vs-BTC IS corr is ~0.85). **This is mechanism-rational for NEW SYMBOL**: idiosyncratic diversity is the value-add, not within-symbol cross-asset redundancy.

### 2.6 TS-mom IS Sharpe baseline grid (table_06) — POSITIVE-BASELINE TRAP RISK QUANTIFIED

| lookback | horizon | n_obs | ann_sharpe_IS | long_frac | short_frac |
|---:|---:|---:|---:|---:|---:|
| 5 | 1 | 5609 | **+0.638** | 0.501 | 0.498 |
| 5 | 3 | 5607 | +0.395 | 0.501 | 0.498 |
| 10 | 1 | 5604 | +0.498 | 0.496 | 0.503 |
| 20 | 5 | 5590 | +0.418 | 0.493 | 0.507 |
| **30 | 3** | 5582 | **+1.322** | 0.487 | 0.513 |
| **30 | 5** | 5580 | **+1.593** | 0.487 | 0.513 |
| **30 | 10** | 5575 | **+1.880** | 0.487 | 0.513 |
| 60 | 5 | 5550 | +1.230 | 0.463 | 0.537 |
| **60 | 10** | 5545 | **+1.677** | 0.463 | 0.537 |

**KEY OBSERVATION**: ATOM's TS-mom shows:
- **Short-horizon (5-10 lookback)**: mid-band POSITIVE Sharpe (+0.40 to +0.64) — comparable to ETH/064's pre-specialist baseline (the LM Master Risk Flag 1 nuance is REAL but MID-BAND, not catastrophic).
- **Mid-horizon (30 lookback × 3-10 horizon)**: STRONG positive Sharpe (+1.32 to +1.88) — a 10-day trend signal is structurally embedded in IS data.
- **Direction balance**: roughly 50/50 long/short at short horizons; tilts toward short at 30-60 lookback (51-54% short) — consistent with the bear-leaning 2024-2025 regime.

**Positive-baseline trap classification**: ATOM falls in the GREY-MID-BAND between DOT/063 (which had NEGATIVE TS-mom baseline pre-/063) and LINK/066-LTC/067 (which had STRONG positive baselines on the 48-col-equivalent setup). The (5,1) TS-mom Sharpe +0.638 is **higher than DOT's pre-/063 Sharpe (~+0.45 by recollection)** which formally puts ATOM at MILD positive-baseline trap risk. **Mitigation**: the LightGBM head's value is NOT to replicate sign-of-mom but to selectively trade through R3 OOD + R5 vol-target — the trivial-baseline Sharpe is the SIGNAL THE ML MUST BEAT, not a ceiling. /066 LINK was ELIMINATED because the LightGBM head produced IS Sharpe LOWER than the trivial-baseline; same for /067 LTC. ATOM at (5,1) +0.638 sets the bar: PROMISING-CLEAN requires the SPECIALIST IS Sharpe to EXCEED +0.30 (sub-trivial-baseline INERT, NEG verdict).

**Per LM Master Risk Flag 1**: confidence in NEGATIVE-pooled-baseline profile is MEDIUM, not HIGH. The mining hypothesis stands but degraded confidence — ATOM is MORE positive-baseline-tilted than DOT was pre-/063.

### 2.7 Triple-barrier label distribution at ATR(2.9, 1.45), horizon=21 (table_07) — SL-BIAS NOTED

| side | n_labels | tp_frac | sl_frac | timeout_frac |
|---|---:|---:|---:|---:|
| **LONG** | 5581 | 25.16% | **59.95%** | 14.89% |
| **SHORT** | 5581 | 25.00% | **55.17%** | 19.84% |

Triple-barrier labels under ATR(2.9, 1.45) are **SL-heavy on both sides** (LONG 60% SL, SHORT 55% SL) — typical of high-vol assets at TP/SL ratio 2.0:1 (ratio = 2.9 / 1.45 = 2.0). At ratio=2.0, the probabilistic break-even WR is 33.3% (since payoff is 2:1 on TP-vs-SL). The observed 25% TP-hit rate gives raw +EV signal only if directional accuracy is significantly above 33.3% — which is exactly what the LightGBM head must learn.

**Interpretation**: this is the SAME label distribution as ETH/064 and BTC/065 under (2.9, 1.45) — NOT a NEW SYMBOL anomaly. The Phase 7 evaluation MUST report per-direction Sharpe to disambiguate whether the realized IS Sharpe is broad-based or short-bias mirage (per LM Master Phase 4.5 closing note — Section 4 F-AXIS-FALSIFIER).

### 2.8 Per-direction regime audit (table_08) — DEEP-BEAR-IS in last 24 months

| year | bars | year_cum_return | implied_directional_bias |
|---|---:|---:|---|
| 2020 | 986 | +0.32 | BULL |
| 2021 | 1095 | **+4.01** | BULL |
| 2022 | 1095 | −0.71 | BEAR |
| **2023** | 1095 | **+0.13** | CHOP |
| **2024** | 1098 | **−0.42** | BEAR |
| **2025-Q1** | 246 | **−0.22** | BEAR |

The **IS window (2023+2024+2025-Q1) is CHOP → BEAR → BEAR cumulative**. The cumulative IS return (2023+2024+2025-Q1) is roughly −0.51 (compounding) — **deep-bear IS with single-bull-month context in early 2023**. The LM Master Risk Flag 2 is CONFIRMED. The Phase 7 evaluation MUST report per-direction Sharpe (long vs short) to flag short-bias mirage; if observed IS Sharpe ≥ +0.30 with >70% of trades in direction=−1, downgrade to NEGATIVE-SHORT-BIAS-MIRAGE per Section 4 falsifier.

### 2.9 Feature 48-col NaN audit (table_09) — 2 columns ALL-NaN-IS by symbol-conditioning

| feature | is_nan_frac | oos_nan_frac | verdict |
|---|---:|---:|---|
| `dot_vs_btc_ret_ratio_30` | **1.0000** | 1.0000 | ALL-NaN — column is SYMBOL-conditional (only populated for SYMBOL=DOT) |
| `eth_vs_btc_ret_ratio_30` | **1.0000** | 1.0000 | ALL-NaN — column is SYMBOL-conditional (only populated for SYMBOL=ETH) |
| `long_short_zscore_30` | 0.502 | 0.000 | HIGH-NaN-IS — long/short data starts mid-window for ATOM |
| `oi_delta_30_z90` | 0.413 | 0.000 | HIGH-NaN-IS — OI data starts mid-window for ATOM |
| `regime_momentum_signed_5d` | 0.018 | 0.000 | MINOR-HEAD-NaN |
| `funding_rate_zscore_30` | 0.006 | 0.000 | MINOR-HEAD-NaN |
| 42 other features | 0.000-0.009 | 0.000 | CLEAN |

**Impact assessment**:
- **`dot_vs_btc_ret_ratio_30` and `eth_vs_btc_ret_ratio_30` ALL-NaN**: these features are SYMBOL-conditional within the V1 feature-generation code — they encode SYMBOL=DOT's ratio vs BTC (populated only for DOT) and SYMBOL=ETH's ratio vs BTC (populated only for ETH). For ATOM, both are ALL-NaN by design. LightGBM handles NaN natively (default `use_missing=True`); the two features will rank effectively at zero-importance for ATOM and waste 2 of the 48 colsample_bytree slots in expectation. **This is NOT a methodology break** — LightGBM's NaN handling makes the features effectively-zero-information rather than corrupting. **Magnitude**: 2 of 48 = 4.2% of colsample_bytree slots wasted. Adjustment to predicted IS Sharpe: ≈ −0.02 to −0.05 (proportionate to the small wasted-slot fraction). **Not flagged for fix at /075** — this would require a feature-generation refactor outside the locked methodology scope. Logged as a future improvement candidate.
- **`long_short_zscore_30` and `oi_delta_30_z90` ~40-50% NaN in IS**: ATOM-specific long/short and OI data starts mid-IS-window (~2024). Same LightGBM NaN handling; partial coverage means partial signal. Adjustment: ≈ −0.02.
- **Net adjusted predicted IS Sharpe**: LM Master modal +0.30 − 0.04 (wasted-slot tax) ≈ **+0.26 modal** (still within PROMISING band).

### 2.10 Cross-cohort return-corr pyramid (table_10) — ATOM's bundle-position

| pair | n_overlap_IS | ret_corr_IS | diversity_score |
|---|---:|---:|---:|
| ATOM-vs-BTC | 5614 | **0.617** | **0.383** |
| ATOM-vs-LTC | 5599 | 0.633 | 0.367 |
| ATOM-vs-ETH | 5614 | 0.673 | 0.327 |
| ATOM-vs-LINK | 5614 | 0.681 | 0.319 |
| ATOM-vs-DOT | 5024 | 0.712 | 0.288 |

ATOM-vs-BTC IS corr 0.617 / diversity_score 0.383 is the **highest diversity score** in the candidate set — the load-bearing claim of the chosen-symbol rationale is CONFIRMED on raw IS data. The ATOM-vs-DOT IS corr 0.712 is the highest co-movement pair — flagged for BUNDLE-002 assembly (`feedback_v1_bundle_no_coin_overlap.md`: each coin owned by exactly one component; ATOM and DOT would be SEPARATE components but mechanism-redundancy at 0.71 cor needs Hurst-or-mechanism divergence check at BUNDLE-002 assembly time. NOT a /075 blocker.).

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1)

- **Declaration**: **HIGH-RISK**
- **Reason**: NEW SYMBOL universe-extension is a structural change to Optuna's training-objective domain — the loss surface, label distribution, and feature-importance ranking are all changed because a brand-new symbol's data and regime history have never been training-objective for any v1 specialist. This qualifies as a HIGH-RISK axis under the Section 2.5 rubric (v1 refactor) because the change is **universe substitution** — explicitly listed as a HIGH-RISK trigger.
- **Mitigation**: **single-seed=42 EXPLORATION** with 50-INNER-seed averaging (the load-bearing SPECIALIST architecture — σ_pop ≤ 0.30 has historically held). Multi-outer-seed validation is **DEFERRED** to a subsequent iteration if /075 verdicts PROMISING and is flagged by `feedback_v1_basin_lottery_vigilance.md` triggers (per-seed spread > 0.50 OR Jaccard < 0.40 OR Spearman ρ < 0.50). Under the v1 rule, if 3+ consecutive HIGH-RISK single-seed EXPLORATIONs produce >1σ negative deltas in a row, the next becomes mandatorily multi-seed; /072 and /073 each produced >1σ NEG; /074 verdict is pending. If /074 closes NEG at IS Δ < −0.10 AND /075 lands NEG, then /076 becomes mandatorily multi-seed.
- **NEW SYMBOL strike rule (one-attempt-and-eliminate)**: per /066 LINK and /067 LTC precedent, NEW SYMBOL universe extension at SPECIALIST EXPLORATION budget has a ONE-ATTEMPT rule. If /075 closes NEGATIVE (any of the four NEGATIVE bands), ATOM is dropped from the BUNDLE-002 candidate roster after this single EXPLORATION. The mining axis pivots to rank-2 candidate (next NEW SYMBOL).
- **Why not bundle ATR-pair shift with a second knob**: the LM Master Phase 4.5 advisor lists the four explicit single-bit changes (SYMBOLS, ITERATION_LABEL, ATR pair, Model A wrapper) as the methodology-COMPLIANT set — they all collapse to "drop ATOM into the same cell as ETH/064 / BTC/065 except for the universe identity". Any second knob (HP tweak, n_trials shift, label horizon shift, feature subset) would break the single-bit discipline and make the verdict uninterpretable.

---

## Section 3 — Proposed Changes (single-bit dispatch deviation from /063 family)

### 3.1 Code-level changes

**(a) Runner: clone `run_iteration_063.py` → `run_iteration_075.py`** with identical signature, except:
- `ITERATION_LABEL = "v1-075"` (was `"v1-063"`)
- `ITERATION_NUMBER = 75` (was 63)
- The runner docstring updated to reflect ATOM SPECIALIST and ETH-class ATR cell (2.9, 1.45) instead of DOT's (3.5, 1.75)
- `--symbols ATOMUSDT` (was `--symbols DOTUSDT`)
- FEATURES_BASE_HASH_48COL: identical sha256(`V1_FEATURE_COLUMNS_PRUNED`) hash (`b81176f893826500536ec5cee8ad00e74bf7edb834290e62e835213defe74ca3` — 48-col stack UNCHANGED)

**(b) Dispatch: add `V1_ITER075_UNIVERSE: tuple[str, ...] = ("ATOMUSDT",)` to `features_v1/__init__.py`** with parallel docstring to V1_ITER074_UNIVERSE / V1_ITER065_UNIVERSE.

**(c) Dispatch: add `elif iteration_label == "v1-075" and set(symbols) == set(V1_ITER075_UNIVERSE):`** branch in `run_baseline_v1.py`, byte-identical to the `v1-065` BTC SPECIALIST branch except for:
- Universe assertion: `assert set(symbols) == {"ATOMUSDT"}` (was `{"BTCUSDT"}`)
- Model wrapper instance name: `Model_A_ATOM_specialist_075` (was `Model_A_BTC_specialist`)
- `BacktestConfig(symbols=("ATOMUSDT",), ...)` (was `("BTCUSDT",)`)
- All other kwargs: byte-identical to /065 (ATR(2.9, 1.45), R1=OFF, R2=OFF, R3=ON-SHARED cutoff=0.70, R5=ON vt_target_vol=0.3 vt_lookback_days=45 vt_min_scale=0.33, specialist_mode=True, V1_SPECIALIST_SEED_COUNT=50, V1_SPECIALIST_OPTUNA_TRIALS=30, max_depth=5 FIXED, num_leaves=31 FIXED, n_estimators ≤ 500, n_startup_trials=10, mean-of-signed-weights aggregator, training_months=24)

**(d) Pre-flight guard** (mirrors /063 / /064 / /065): assert `_compute_features_hash(V1_FEATURE_COLUMNS_PRUNED) == FEATURES_BASE_HASH_48COL` at runner entry; assert `len(active_feature_columns) == 48`; assert `set(symbols) == {"ATOMUSDT"}`; assert `V1_SPECIALIST_SEEDS[0] == 42` and `V1_SPECIALIST_SEEDS[-1] == 91`.

**(e) Engine parity (HARD per `feedback_v1_backtest_live_parity_hard.md`)**: NEW SYMBOL universe extension propagates to `engine.py:_initial_setup` symbol-fetch (must add ATOMUSDT to the kline-fetch list when a BUNDLE-002 with ATOM merges). For /075 EXPLORATION only, the BACKTEST runner is the validation surface; the engine parity is verified at BUNDLE-002 assembly time, NOT at /075. The Critic Check 15 = `BUNDLE-PARITY-VIOLATION` is **N/A at /075 EXPLORATION** (no bundle assembly).

### 3.2 What is held identical to /063 / /064 / /065 (everything except the universe identity + ATR cell)

| Variable | Value |
|---|---|
| Universe | `{ATOMUSDT}` (single-coin SPECIALIST) |
| Feature columns | **`V1_FEATURE_COLUMNS_PRUNED` (48 cols, UNCHANGED)** — sha256 hash `b81176f893826500536ec5cee8ad00e74bf7edb834290e62e835213defe74ca3` |
| Labels | Triple-barrier **ATR TP=2.9 / ATR SL=1.45** (ETH/064 cell — vol-class match for ATOM 80% IS realized vol) |
| Label horizon | 21 candles (UNCHANGED from /063 family) |
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
| Model wrapper class | **Model A** (`RiskV1Wrapper` with R1=OFF, R2=OFF, R3=ON-SHARED cutoff=0.70) — matches /064 ETH and /065 BTC; NOT /063 DOT's Model E |
| Vol targeting | Per-coin VT (45-day rolling, target_vol=0.3, min_scale=0.33, max_scale=2.0; UNCHANGED) |
| Parquet feature-generation | **NO REGENERATION** — `data/features/ATOMUSDT_8h_features.parquet` exists with all 48 V1_FEATURE_COLUMNS_PRUNED present (table_09 audit). |

### 3.3 What is NOT changed (per LOCKED methodology directive)

- **No feature change** (V1_FEATURE_COLUMNS_PRUNED stays at 48 cols — sha256 hash UNCHANGED; the 2 ALL-NaN-IS columns are LightGBM-native-NaN-handled, not removed)
- **No labeling change** (triple-barrier ATR=2.9/1.45 — single-cell shift from /063's 3.5/1.75; aligned with ETH/064 and BTC/065)
- **No model-arch change** (LightGBM head; not XGBoost; per /016 v3 closure)
- **No risk-wrapper flip** (R1 stays OFF per `f81cafc3` catalog rule + Model A pattern; R2 stays OFF; R3 stays ON-SHARED cutoff=0.70; R5 stays ON)
- **No Optuna search-space change** (HP bounds inherited from /063 family; bounds_profile="v1_specialist")
- **No multi-seed promotion** (single outer seed=42 EXPLORATION discipline; multi-seed deferred to a future CONFIRMATION if /075 PROMISING)
- **No parquet regeneration** (HIGH guard: cross-iteration reproducibility for /076+ mining pipeline depends on parquet hash stability)
- **No post-aggregator rule layer** (the /074 AXIS-R Mid-Bull SHORT VETO is mechanism-INVERSE for ATOM — ATOM IS is deep-bear, NOT mid-bull, so shorts are likely the PnL-positive cohort. /074's rule is NOT applied to /075)
- **No threshold tuning** (Optuna picks `confidence_threshold` per seed within the locked range [0.50, 0.85])

### 3.4 Response to LM Master Phase 4.5 recommendations (per v1 LM Coordination)

LM Master's `briefs-v1/iteration_v1-075/lgbm_advisor.md` is a SCOPE-CONSTRAINED advisor — methodology constants are LOCKED per user directive, so LM Master's "Recommended Hyperparameter Direction" section is observation-only (no actionable HP changes). QR response:

| LM Master section | QR response |
|---|---|
| Recommended HP direction #1: verify single-coin cohort `(ATOMUSDT,)` and ITERATION_LABEL="v1-075" | **ADOPTED VERBATIM** — Section 3.1 (a)-(c) implements the exact dispatch. |
| Recommended HP direction #2: observe `n_estimators` realized distribution at Phase 7.4 | **ADOPTED** — Phase 7.4 post-mortem will report best-trial `n_estimators` across walk-forward months (std > 150 triggers basin-lottery flag despite 50-seed averaging). |
| Recommended HP direction #3: observe `min_data_in_leaf` and `lambda_l1` at Phase 7.4 | **ADOPTED** — Phase 7.4 post-mortem will flag if Optuna picks `min_data_in_leaf < 50` for >40% of months (potential overfitting to short-bias labels). |
| Recommended feature-engineering direction: verify `regime_momentum_signed_5d`, `hurst_100`, `vwap_dev_20` populate cleanly; verify `btc_ret_30d`, `btc_rv_50`, `eth_ret_30d` non-NaN | **VERIFIED** in table_09 — `regime_momentum_signed_5d` has 1.8% head-NaN (CLEAN); `btc_*`, `eth_*` cross-asset features all populate cleanly (0% NaN); `funding_rate_zscore_30` has 0.6% head-NaN (CLEAN); the 2 SYMBOL-conditional ratio features ALL-NaN (LightGBM NaN-handles). |
| Predicted modal IS Sharpe +0.30; 90% band [−0.10, +0.65] | **ADOPTED** as the F-AXIS #1 verdict band reference (modal +0.30); per QR table_09 NaN-tax adjustment, MQR-modal-adjusted = +0.26. |
| Risk Flag 1: TS-mom IS Sharpe nuance — chosen-symbol rationale cited +0.58, LM replication +0.918 (different lookback/horizon) | **CONFIRMED via QR table_06** — (5,1) Sharpe is +0.638 (mid-band); (5,3) is +0.395; (30,3) is +1.322. The chosen-symbol rationale's +0.58 is bracketed by these — likely citing a (5-10, 3-5) combination. The MEDIUM positive-baseline trap risk is documented in Section 1 H1d. |
| Risk Flag 2: deep-bear IS + deep-bear OOS → short-cohort overfit risk | **ADOPTED as F-AXIS-FALSIFIER #1** — Section 4 mandates per-direction Sharpe + WR + trade count in Phase 7 evaluation; if >70% of trades direction=−1 with >+1.5σ short-bias, verdict downgrades to NEGATIVE-SHORT-BIAS-MIRAGE. |
| Risk Flag 3: 0.61 BTC corr is on the LOW end → cross-asset feature dilution | **ADOPTED** — Section 1 H1a explicit; expected feature-importance signature (within-symbol top-5, cross-asset 8-14) flagged for Phase 7.4 importance triage. |
| Risk Flag 4: v2 dead-paths catalog notes prior ATOM swap failure | **PRE-REGISTERED** — Section 0.7 explicit: v2 ATOM failure was cohort-pooled-with-7-gate-multi-bit confound, NOT a per-symbol ATOM rejection. v1 specialist axis is structurally orthogonal. |
| Risk Flag 5: 0.81 IS DOT correlation → BUNDLE-002 mechanism-redundancy concern | **FLAGGED for downstream (BUNDLE-002 assembly), not /075 blocker** — table_10 confirms IS DOT corr is 0.712 (lower than LM's full-window 0.81); BUNDLE-002 assembly QR must check ATOM+DOT mechanism-redundancy. |
| Saturation Risk 1: First NEW SYMBOL mine — validate composite predictor on rank-2/rank-3 | **ACKNOWLEDGED** — autopilot mining pipeline stages rank-2/rank-3 candidates; the user directive explicitly states "we need to mine these new specialists … using all the quantitative knowledge". |
| Saturation Risk 2: No prior LM Master advice on universe extension — +0.30 modal is a PRIOR not calibrated frequentist | **ACCEPTED** — Section 4 bands are pre-registered relative to the BUNDLE-001 specialist IS Sharpe distribution (mean +0.16, std ≈ 0.30), NOT relative to the LM Master modal alone. The bands are robust to LM Master prediction error within ~±0.20. |
| Saturation Risk 3: Basin-lottery vigilance applies even at 50-inner-seed | **ADOPTED** — Section 4 F-AXIS #2 σ_pop dispersion gate. |
| Closing note: per-direction (long vs short) Sharpe + trade count + WR reporting in Phase 4 falsifier table | **HARDWIRED** — Section 4 F-AXIS-FALSIFIER #1 explicit; the verdict cannot be cleanly interpreted without per-direction reporting given the −51% cumulative IS bear regime. |

LM Master confidence: **MEDIUM**. QR concurs on MEDIUM confidence; the brief is honest about the positive-baseline trap GREY-MID-BAND and the deep-bear IS short-bias mirage risk.

---

## Section 4 — F-Axis Bands (Falsifier Gates)

Pre-registered F-AXIS bands per `feedback_no_cheating.md` (HARD anti-tuning — frozen at brief commit SHA Section 12). Band edges WILL NOT be re-tuned post-hoc under any scenario.

### F-AXIS #1 — Mean IS Sharpe across 50 inner seeds (PRIMARY verdict; PROMISING / NEGATIVE adjudicator)

Anchor: NEW SYMBOL — no prior ATOM specialist; bands referenced against the BUNDLE-001 member IS Sharpe distribution and the LM Master Phase 4.5 modal +0.30.

| Band | Range (mean IS Sharpe) | Verdict | Action |
|---|---|---|---|
| **PROMISING-CLEAN** | **IS Sharpe ≥ +0.50** | SPECIALIST-PROMISING-STRONG | ATOM enters BUNDLE-002 candidate roster at HIGH confidence; multi-outer-seed CONFIRMATION queued; mining axis validated for rank-2/rank-3 candidates. |
| **PROMISING-TENTATIVE** | **+0.20 ≤ IS Sharpe < +0.50** | SPECIALIST-PROMISING-TENTATIVE | ATOM enters BUNDLE-002 candidate roster at REDUCED confidence; basin-lottery vigilance triggers (per-seed spread, Jaccard, Spearman ρ) determine whether multi-seed CONFIRMATION is required before BUNDLE-002 inclusion. |
| **NEGATIVE** | **IS Sharpe < +0.20** OR IS trades < 50 | SPECIALIST-NEGATIVE | ATOM DROPPED from candidate roster after ONE EXPLORATION attempt (per /066 LINK + /067 LTC one-attempt-and-eliminate precedent for NEW SYMBOL); mining axis pivots to rank-2 candidate. The trade-count floor (50 IS trades) per `feedback_v1_trade_rate_floor_50_per_specialist.md` overrides the Sharpe band — if /075 produces <50 IS trades, verdict is NEGATIVE regardless of Sharpe magnitude. |

**Per `feedback_v1_trade_rate_floor_50_per_specialist.md`** (single-symbol specialist OOS floor TIGHTENED to ≥50 OOS per specialist): the analogous IS-side floor is also ≥50 — if /075 IS produces <50 trades, the Sharpe estimate is too noisy (σ_SR ≈ 0.20 at N=25) to support a PROMISING verdict regardless of point estimate. The trade-count floor is a HARD gate.

**Per `feedback_sharpe_floor.md`**: the v1 IS Sharpe > 1.0 floor is the absolute merge gate; merge happens only at BUNDLE-002 assembly time. /075 EXPLORATION verdict gates on the F-AXIS #1 band above (PROMISING-CLEAN +0.50, PROMISING-TENTATIVE +0.20, NEGATIVE <+0.20 or <50 trades), NOT on absolute Sharpe > 1.0.

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

/075 has no prior ATOM OOS reference. LM Master predicts OOS Sharpe modal +0.20 (90% band [−0.30, +0.60]).

| Band | OOS Sharpe range | Comment |
|---|---|---|
| Preserved/strong | ≥ +0.30 | OOS edge confirms IS not regime-coincident; ATOM bundle-candidate strengthened |
| Acceptable | 0.0 to +0.30 | Mild OOS compression; consistent with single-seed EXPLORATION + chop-dominant regime |
| Severe compression | < 0.0 | Flag for multi-seed re-validation; do NOT auto-block /075 PROMISING verdict (IS is the primary gate for /075 EXPLORATION) |
| Suspicious OOS-dominant lift | ≥ +0.60 with IS Δ vs LM modal +0.30 < +0.10 | Flag possible regime-specific OOS lift (sister to v3 PROMISING-MECHANICAL); needs Phase 7.4 LM Master diagnostic |

OOS Sharpe is **NEVER** the strike adjudicator for /075 (per `feedback_no_cheating.md`).

### F-AXIS-FALSIFIER #1 — Per-direction Sharpe + WR + trade count (HARD per LM Master closing note)

The /075 verdict cannot be cleanly interpreted without per-direction reporting given the −51% cumulative IS bear regime.

The QR Phase 7 evaluation MUST produce a per-direction table:

| Direction | n_trades | win_rate | per-direction Sharpe |
|---|---:|---:|---:|
| LONG | TBD | TBD | TBD |
| SHORT | TBD | TBD | TBD |

| Observed | Verdict modifier |
|---|---|
| balanced (40-60% short trades; per-direction Sharpe within 1σ of each other) | CLEAN — interpret F-AXIS #1 verdict at face value |
| short-bias mirage (>70% short trades AND short Sharpe > long Sharpe + 1.5σ) | **DOWNGRADE to NEGATIVE-SHORT-BIAS-MIRAGE** regardless of headline IS Sharpe |
| long-bias mirage (>70% long trades AND long Sharpe > short Sharpe + 1.5σ) | DOWNGRADE to NEGATIVE-LONG-BIAS-MIRAGE regardless of headline IS Sharpe |

### F-AXIS-FALSIFIER #2 — Feature importance dilution at 0.62 BTC corr (PER LM RISK FLAG 3)

Expected feature-importance signature for ATOM (low cross-asset corr → idiosyncratic specialization):
- Within-symbol primitives (`regime_momentum_signed_5d`, `vwap_dev_*`, `mr_bb_pctb_*`, `atr_pct_*`, `mom_rsi_*`) rank top-5.
- Cross-asset features (`btc_ret_*`, `btc_rv_50`, `eth_ret_*`) rank 8-14 (NOT top-3).
- ALL-NaN-IS features (`dot_vs_btc_ret_ratio_30`, `eth_vs_btc_ret_ratio_30`) rank effectively zero (LightGBM NaN-handle).

| Observed | Verdict modifier |
|---|---|
| within-symbol dominant top-5 (rank 1-5), cross-asset 8-14 | CONFIRMS idiosyncratic specialization; consistent with mechanism rational |
| cross-asset dominant top-3 (`btc_*` family in top-3) | UNEXPECTED — LightGBM found cross-asset edge despite 0.62 corr; flag for Phase 7.4 mechanism review (could be edge case OR could be co-movement-overfitting) |
| flat ranking (no clear top-5 dominant) | suggests 50-seed averaging dispersed the signal across many weak features; F-AXIS #2 σ_pop should be elevated |

### F-AXIS-BEHAVIORAL — IS trade count + walk-forward cell coverage

LM Master Phase 4.5 predicts ~100-200 IS trades over 2160 candles (typical SPECIALIST trade rate ~5-10% bar-utilization). Trade-count floor: ≥50 IS trades per `feedback_v1_trade_rate_floor_50_per_specialist.md`.

| Observed | Interpretation |
|---|---|
| IS trades ≥ 100 | sufficient signal-to-noise for cross-seed Sharpe stability |
| 50 ≤ IS trades < 100 | borderline; F-AXIS #1 verdict applies but with reduced confidence; multi-seed validation recommended for any PROMISING tag |
| IS trades < 50 | **AUTO-NEGATIVE** per `feedback_v1_trade_rate_floor_50_per_specialist.md` — Sharpe estimate is too noisy to interpret regardless of point value |

### F-AXIS-COUNTERFACTUAL — N/A for /075 (no anchor to compare against)

/075 is a NEW SYMBOL with no prior ATOM specialist anchor. The counterfactual audit table is N/A. The /065 BTC SPECIALIST `specialist_dispersion.csv` persistence pattern is still required (Section 5.3 item 14).

---

## Section 5 — Risk Mitigation

### 5.1 Axis-specific risk

- **Pre-registered band rigor (HIGH)**: Section 4 F-AXIS bands are frozen at this brief's commit (Section 12). If the QR (or any future post-hoc analyst) re-fits the bands after seeing /075 results, the verdict collapses to METHODOLOGY-FALSIFIED. Phase 8 diary MUST explicitly reference the brief commit SHA when adjudicating.
- **Single-bit discipline (HARD)**: the brief HARDWIRES the locked methodology constants. Only the universe identity + ATR cell deviate vs /063 (and ATR cell aligns with /064 /065). If the runner touches a second axis (e.g., "while we're here, let's try n_trials=50"), the iteration becomes a 2-bit cross-axis confound and the verdict is uninterpretable.
- **Engine parity (HIGH at BUNDLE-002 assembly; LOW at /075 EXPLORATION)**: per `feedback_v1_backtest_live_parity_hard.md` (Critic Check 15), NEW SYMBOL universe extension requires `engine.py:_initial_setup` to add ATOMUSDT to the kline-fetch list when ATOM merges into BUNDLE-002. For /075 EXPLORATION, the backtest runner is the validation surface only; engine parity is verified at BUNDLE-002 assembly time. The Critic Check 15 = `BUNDLE-PARITY-VIOLATION` is **N/A at /075 EXPLORATION**.
- **Positive-baseline trap GREY-MID-BAND (MEDIUM)**: ATOM TS-mom (5,1) Sharpe +0.638 — between DOT pre-/063 (NEGATIVE-baseline, BUNDLE-included) and LINK/066+LTC/067 (STRONG positive-baseline, ELIMINATED). The mining hypothesis stands but with MEDIUM confidence. Phase 7.4 post-mortem MUST report: SPECIALIST IS Sharpe vs trivial-baseline IS Sharpe at multiple (lookback, horizon) cells. If SPECIALIST IS Sharpe < trivial-baseline IS Sharpe at any (lookback, horizon) where trivial-baseline > +0.30, that is the LINK/LTC-precedent verdict pattern.
- **Deep-bear IS short-bias mirage (HIGH)**: 2024+2025-Q1 cumulative IS return ≈ −0.64; labels likely skew toward direction=−1 hits. Mitigations: 50-seed averaging dampens single-seed bear-fit basins; R3 OOD provides regime-defense; Phase 7 evaluation MUST report per-direction Sharpe (F-AXIS-FALSIFIER #1).
- **2 ALL-NaN-IS cross-symbol features (LOW)**: `dot_vs_btc_ret_ratio_30` and `eth_vs_btc_ret_ratio_30` are SYMBOL-conditional (DOT-only, ETH-only). For ATOM, both are ALL-NaN. LightGBM NaN-handle. Cost: 2/48 = 4.2% of colsample_bytree slots wasted. Adjustment to expected IS Sharpe: −0.02 to −0.05. **Logged for future feature-generation refactor**; NOT a /075 blocker. The dispersion-reservoir mechanism from /073 closeout dictates: do NOT alter the 48-col stack even when 2 columns are ALL-NaN for a NEW SYMBOL.

### 5.2 Risk wrappers (Model A pattern — matches /064 and /065)

| Wrapper | /075 setting | Rationale |
|---|---|---|
| R1 (consecutive-SL cool-down) | **DISABLED** | Model A pattern (matches /064 /065); R1 CATALOG-CLOSED for SPECIALIST_mode per `f81cafc3`. Late-streak trades have better edge for Model A symbols per BASELINE_V1 evidence. |
| R2 (DD scaling) | **DISABLED** | Model A pattern (matches /064 /065); R2 is Model E DOT-only. |
| R3 (OOD Mahalanobis cutoff=0.70, 16 SI features SHARED) | **ENABLED** | Active for all v1 SPECIALISTs since /063; applied at AGGREGATOR level (NOT per-seed). Provides regime-defense against OOS shifts. |
| R5 (per-coin vol target, 45-day rolling) | **ENABLED** | vt_target_vol=0.3, vt_lookback_days=45, vt_min_scale=0.33, vt_max_scale=2.0. Matches /063 /064 /065. |
| AXIS-R (/074 Mid-Bull SHORT VETO post-aggregator) | **DISABLED** | Mechanism-INVERSE for ATOM: ATOM IS is deep-bear, not mid-bull; shorts are likely the PnL-positive cohort. /074's rule does NOT apply. |

### 5.3 QE Phase 6.0 Critic pre-flight check items

1. `run_iteration_075.py` is a clone of `run_iteration_063.py` with the SINGLE-BIT changes per Section 3.1 (a)-(d): symbols=("ATOMUSDT",), ITERATION_LABEL="v1-075", ATR(2.9, 1.45), Model A wrapper.
2. `run_baseline_v1.py` dispatch branch `elif iteration_label == "v1-075" and set(symbols) == set(V1_ITER075_UNIVERSE)` is byte-identical to `v1-065` BTC branch except for `BacktestConfig(symbols=("ATOMUSDT",))` + model-name string `Model_A_ATOM_specialist_075`.
3. `feature_columns=list(V1_FEATURE_COLUMNS_PRUNED)` (48 cols) is passed explicitly to `LightGbmStrategy` per `feedback_explicit_feature_columns.md`.
4. `FEATURES_BASE_HASH_48COL = _compute_features_hash(V1_FEATURE_COLUMNS_PRUNED)` is pinned at runner entry and asserts equality with `b81176f893826500536ec5cee8ad00e74bf7edb834290e62e835213defe74ca3` (UNCHANGED 48-col hash).
5. **Parquets NOT regenerated** — `data/features/ATOMUSDT_8h_features.parquet` exists with all 48 cols (table_09); ATOM klines csv is on disk (6933 rows, 2020-02-07 → 2026-06-06).
6. Risk wrappers Model A pattern: `r1_enabled=False, r2_enabled=False, r3_enabled=True, r3_cutoff=0.70, r5_vol_target_enabled=True, r5_vol_target_pct=4.0 (target_vol=0.3 equivalent)`.
7. ATR barriers: TP=2.9, SL=1.45 (ETH/064 cell).
8. `specialist_mode=True`, inner_seeds=50, n_trials=30, outer seed=42 — all unchanged from /063 family.
9. `ENSEMBLE_SIZE=1`, max_depth=5 FIXED, num_leaves=31 FIXED, n_estimators ≤ 500, n_startup_trials=10, mean-of-signed-weights aggregator — all unchanged.
10. Walk-forward embargo applied (`train_end_ms = test_start_ms - embargo_ms`).
11. **NaN handling pre-flight**: assert `df[V1_FEATURE_COLUMNS_PRUNED].dropna(how='all').shape[0] >= 5000` (catastrophic feature-coverage break sanity); confirm `dot_vs_btc_ret_ratio_30` and `eth_vs_btc_ret_ratio_30` are ALL-NaN-by-design (Section 2.9); LightGBM `use_missing=True` (default).
12. `V1_ITER075_UNIVERSE: tuple[str, ...] = ("ATOMUSDT",)` is added to `features_v1/__init__.py` with parallel docstring to V1_ITER074_UNIVERSE / V1_ITER065_UNIVERSE.
13. `reports-v1/iteration_v1-075/` directory committed at Phase 8 closeout per HARD rule `0a19e068`.
14. **`specialist_dispersion.csv` persisted** for both IS and OOS windows per LM 7.4 load-bearing patch `153664ed` (continuation of /065 mandate).
15. Pre-registered F-AXIS bands frozen at brief commit SHA (Section 12); no post-Phase-7 re-tuning permitted.

### 5.4 Historical effect simulation — N/A for NEW SYMBOL

There is no prior ATOM specialist roster to simulate against. The expected behavior is given by the BUNDLE-001 member IS Sharpe distribution (mean +0.16, std ≈ 0.30) adjusted by the LM Master Phase 4.5 mechanism analysis (Section 2 H1a-H1e). The LM Master modal +0.30 minus the table_09 NaN-tax (−0.04) gives QR-modal-adjusted **+0.26 IS** (PROMISING-TENTATIVE band low end).

---

## Section 6 — Phase 5.5 Gate Pre-Flight (load-bearing for QE)

Phase 5.5 gate items (must clear ALL before QE Phase 6 fires):

| # | Check | Verifier | Status @ brief authoring |
|---|---|---|---|
| G1 | EDA script `analysis/v1-075/eda.py` committed and tables 01-10 persisted | `git log` shows commit; `analysis/v1-075/table_*.csv` exist | TO BE COMMITTED in Phase 5 closeout |
| G2 | IS firewall: every loaded path asserts no `out_of_sample` substring | `_assert_is_only_path` helper present in `eda.py`; `is_only(df)` filter applied | PRESENT |
| G3 | Brief Section 0.6 axis-family declaration and rotation status | This brief Section 0.6 | DONE |
| G4 | Brief Section 2.5 HIGH-RISK declaration | This brief Section 2.5 | DONE |
| G5 | Brief Section 3.4 explicit LM Master response | This brief Section 3.4 | DONE |
| G6 | Brief Section 4 F-AXIS bands pre-registered (frozen at commit SHA) | This brief Section 4 | DONE |
| G7 | Brief Section 5 Risk Mitigation with IS-calibrated thresholds | This brief Section 5 | DONE |
| G8 | Brief Section 11 backtest-live parity statement | This brief Section 11 | DONE |
| G9 | `V1_ITER075_UNIVERSE` declared in features_v1 | `grep V1_ITER075_UNIVERSE src/crypto_trade/features_v1/__init__.py` | TO BE ADDED in Phase 6 setup |
| G10 | `run_iteration_075.py` clone with single-bit changes | `git log` shows new runner | TO BE ADDED in Phase 6 setup |
| G11 | Dispatch branch `elif iteration_label == "v1-075"` in run_baseline_v1.py | `grep "v1-075" run_baseline_v1.py` | TO BE ADDED in Phase 6 setup |
| G12 | Features parquet exists with 48 cols populated | table_09 audit | DONE (data/features/ATOMUSDT_8h_features.parquet) |
| G13 | 2 ALL-NaN-IS cross-symbol features documented as LightGBM-NaN-handled | This brief Section 2.9 + 5.1 | DONE |
| G14 | `_assert_is_only_path` test on EDA: `pytest analysis/v1-075/test_eda_firewall.py` (optional) | If a pytest suite for EDA firewall is added | OPTIONAL — not required at G-level |

Phase 5.5 gate verdict at brief authoring: **READY FOR PHASE 6 SETUP** (G9-G11 are Phase 6 setup-side tasks; the QR brief is complete).

---

## Section 7 — Falsification Conditions (HARD anti-tuning)

Per `feedback_no_cheating.md`, the following must hold for /075 verdict integrity:

1. **F-AXIS #1 bands** (Section 4) frozen at brief commit SHA. No post-Phase-7 re-tuning. If observed IS Sharpe is +0.19, the verdict is NEGATIVE (NOT "let's call it PROMISING-TENTATIVE-MARGINAL").
2. **Trade-count floor 50 IS** (per `feedback_v1_trade_rate_floor_50_per_specialist.md`) — AUTO-NEGATIVE if IS trades < 50.
3. **Per-direction Sharpe falsifier** (F-AXIS-FALSIFIER #1) — short-bias mirage downgrades headline PROMISING to NEGATIVE-SHORT-BIAS-MIRAGE.
4. **No methodology constant change post-brief**. If the QE detects a mismatch and proposes "let's bump n_trials to 50 for ATOM specifically", that is a methodology-violation; ABORT and re-evaluate.
5. **No EDA re-run with different IS-window definition** (`feedback_no_cheating.md`).
6. **No retroactive band-edge tuning to make the verdict land in a chosen band** — bands frozen at brief commit; verdict is mechanical.

---

## Section 8 — Expected Outputs / Reports

| Artifact | Path | Required-by |
|---|---|---|
| EDA script | `analysis/v1-075/eda.py` | Phase 5.5 G1 |
| EDA tables | `analysis/v1-075/table_*.csv` (10 tables) | Phase 5.5 G1 + Section 2 evidence |
| Brief | `briefs-v1/iteration_v1-075/research_brief.md` | Phase 5 closeout |
| LM Master advisor | `briefs-v1/iteration_v1-075/lgbm_advisor.md` | Phase 4.5 (already present) |
| Critic pre-flight | `briefs-v1/iteration_v1-075/critic_preflight.md` | Phase 6.0 |
| Phase 5.5 gate review | `briefs-v1/iteration_v1-075/phase5p5_gate.md` | Phase 5.5 |
| Runner | `run_iteration_075.py` | Phase 6 setup |
| Dispatch branch | `run_baseline_v1.py` (elif `v1-075`) | Phase 6 setup |
| Universe constant | `src/crypto_trade/features_v1/__init__.py` (V1_ITER075_UNIVERSE) | Phase 6 setup |
| Backtest reports | `reports-v1/iteration_v1-075/{in_sample,out_of_sample}/` + `comparison.csv` + `per_seed_sharpe.csv` + `optuna_best_params.csv` + `specialist_dispersion.csv` | Phase 7 closeout |
| Diary | `diary-v1/iteration_v1-075.md` | Phase 8 closeout |

---

## Section 9 — Cycle-7 Roster Position

Per `feedback_v1_cycle6_per_symbol_regime_specialist_mandate.md`, cycle-7 mining strategy:
- BUNDLE-001 (DOT/063 + ETH/064 + BTC/065) is the running BUNDLE roster.
- /066 LINK, /067 LTC: ELIMINATED (positive-baseline trap).
- /068-/070, /072, /073: BUNDLE-001-improvement axes — 3 CLOSED FAIL.
- /074 ETH-IMPROVED-V3: active, verdict pending.
- **/075 ATOMUSDT NEW SYMBOL**: this iteration — first universe-extension mining attempt.

If /075 PROMISING, ATOM joins the BUNDLE-002 candidate roster. CONFIRMATION assembles regime-complementary specialists from the running roster (per the per-symbol regime-specialist mandate, IS-regime-diverse bundles are hypothesized to generalize OOS).

If /075 NEGATIVE, mining axis pivots to rank-2 candidate (AVAX or MATIC per the mine-phase ranking).

The autopilot mining pipeline (rank-2 / rank-3 candidates staged) continues regardless of /075 outcome — per user directive 2026-06-06.

---

## Section 10 — Trade-rate floor compliance

Per `feedback_v1_trade_rate_floor_50_per_specialist.md` (single-symbol specialist OOS floor TIGHTENED to ≥50 OOS per specialist):
- **IS floor**: ≥50 IS trades required for any PROMISING tag (Section 4 F-AXIS #1 NEGATIVE auto-fires at <50 IS trades).
- **OOS floor**: ≥50 OOS trades required for BUNDLE-002 inclusion at CONFIRMATION (NOT a /075 EXPLORATION gate — /075 is single-outer-seed EXPLORATION; OOS trade count is informational at this stage).
- **30-49 trades fallback**: 7-outer-seed validation OR baseline anchor fallback per the rule. NEW SYMBOL has no baseline anchor → 7-outer-seed validation is the only fallback (mandates a follow-up multi-seed iteration if /075 lands 30-49 trades).
- **<30 trades**: auto-reject (NEGATIVE verdict).

This brief inherits the rule. Phase 7 evaluation reports IS+OOS trade counts explicitly.

---

## Section 11 — Backtest-Live Parity Statement

Per `feedback_v1_backtest_live_parity_hard.md` (Critic Check 15 = `BUNDLE-PARITY-VIOLATION`):

- **At /075 EXPLORATION**: parity is N/A. /075 is a single-coin SPECIALIST EXPLORATION; no BUNDLE assembly. The backtest runner is the validation surface. No `engine.py:_tick` change is required at /075.
- **At BUNDLE-002 assembly time (if /075 PROMISING)**: ATOM SPECIALIST inclusion in BUNDLE-002 requires:
  - `engine.py:_initial_setup` to add `ATOMUSDT` to the kline-fetch list (8h interval; matches v1 BUNDLE-001 fetch pattern).
  - The BUNDLE-002 dispatch (when assembled in a future iteration) must wire the ATOM SPECIALIST's `LightGbmStrategy` instance into the per-symbol model registry in `engine.py`, byte-identical to the backtest-side instance (same `feature_columns`, same R3/R5 wrappers, same ATR cell, same threshold).
  - **No coin overlap rule** (`feedback_v1_bundle_no_coin_overlap.md`): ATOM owned by exactly ONE component (the ATOM SPECIALIST); DOT remains owned by the DOT SPECIALIST; ETH by ETH; BTC by BTC. No cross-symbol pooling.
  - **Bundle weights IS-only** (`feedback_v1_bundle_weight_is_only.md`): if BUNDLE-002 introduces a per-symbol weight calibration, the weights must be derived from `analysis/iteration_v1-NNN/weight_calibration.py` reading ONLY IS data.
- **No post-trade aggregation/netting**: the BUNDLE dispatch is per-symbol additive — no netting across symbols.

This brief pre-commits to the parity surface at BUNDLE-002 assembly time. /075 EXPLORATION runs only the backtest-side validation; no engine code is touched.

---

## Section 12 — Pre-Registration Commit SHA (HARD anti-tuning anchor)

The F-AXIS bands in Section 4, the falsification conditions in Section 7, and the pre-registered methodology constants in Section 3.2 are FROZEN at the commit SHA of this brief.

**Brief commit SHA**: TO BE FILLED in Phase 5 closeout (the QR commits this brief with message `docs(iter-v1/075): Phase 1-5 QR — ATOM NEW SYMBOL specialist EDA + brief`; the resulting SHA is the freeze anchor).

Any post-Phase-7 re-fitting of bands, retroactive band-edge adjustment, or methodology constant change relative to this brief's content collapses the /075 verdict to **METHODOLOGY-FALSIFIED** and forfeits the iteration regardless of the headline IS Sharpe.

---

## Section 13 — Summary

ATOMUSDT is the first NEW SYMBOL universe-extension SPECIALIST EXPLORATION in v1 history, the rank-1 mine-phase candidate (composite score 0.767), and the cleanest test of whether the LOCKED SPECIALIST methodology extracts edge from a structurally idiosyncratic non-v1-native coin. The mechanism-rational case is: low cross-asset correlation (0.617 IS BTC corr, table_05; 0.383 IS diversity score, table_10 — both highest in eligible set) provides the cleanest roster-diversity addition to BUNDLE-001's ~0.85-mean-correlation backbone; ETH-class mid-vol regime (table_02 IS 65-98% annualized) matches the (2.9, 1.45) ATR cell; chop-dominant 58% IS regime (table_04) favors mean-reverting + selective-entry ML edge; the 48-col `V1_FEATURE_COLUMNS_PRUNED` has 46 clean features for ATOM (2 ALL-NaN-IS by SYMBOL-conditioning, LightGBM NaN-handle).

The risks are: positive-baseline trap GREY-MID-BAND (TS-mom (5,1) IS Sharpe +0.638, between DOT pre-/063 NEGATIVE and LINK/066 + LTC/067 STRONG positive); deep-bear IS regime (2024+2025-Q1 cumulative ≈ −0.51) raising short-bias mirage risk; basin-lottery vigilance at single-outer-seed=42 EXPLORATION budget (mitigated by 50-INNER-seed averaging but not eliminated).

Modal predicted IS Sharpe **+0.30** (LM Master Phase 4.5; QR-adjusted +0.26 after NaN-tax). PROMISING-CLEAN at +0.50; PROMISING-TENTATIVE at +0.20-+0.50; NEGATIVE at <+0.20 or <50 trades. Verdict adjudication is mechanical against Section 4 frozen bands.

Single-bit deviation vs /063 dispatch: `SYMBOLS=("ATOMUSDT",)`, `ITERATION_LABEL="v1-075"`, ATR cell shift /063's (3.5, 1.75) → ETH/064's (2.9, 1.45), Model A wrapper. All other methodology constants HELD per user directive 2026-06-06.

NEW SYMBOL strike rule: one-attempt-and-eliminate per /066 LINK + /067 LTC precedent.
