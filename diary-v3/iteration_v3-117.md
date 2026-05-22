# iter-v3/117 — Cycle-6 EXPLORATION slot #8 — CANDLE FREQUENCY: 8h → 24h-multi-offset (3 offsets @ 0h/8h/16h UTC, pooled-with-offset_id LightGBM, 14+1 features) — FILED EXPLORATION-NEGATIVE — the worst /117-style result in cycle-6 history (IS −2.17 / OOS −3.26, Δ IS −2.97 / Δ OOS −3.40 vs the /060 anchor). The pre-registered Section-4 explicit falsifier fires DECISIVELY on both arms; the brief's Section-1 hypothesis is FALSIFIED at production scale; the universe-pooled held-out AUC = 0.5823 (v3's strongest ever) DID NOT TRANSFER through production LightGBM walk-forward training. Mechanism: a 4-part trace — (1) BCH 99.12% label imbalance produces a near-degenerate `predict_proba` calibration where the population AUC is an imbalanced-data artifact, not a discriminative-quality signal; (2) TRX 79 IS-trade book at 24.1% win-rate (below the 33.3% 2:1 ATR breakeven) → ZERO OOS trades — the canonical IS-overfit-to-noise pattern; (3) z-score OOD gate over-fires on LDO at 69.5% kill rate, structurally induced by the pooled-multi-offset architecture (between-offset variance compounded into total std, LDO's small per-offset sample, z=2.0 threshold inappropriate for the heavier-tail-mass pooled distribution); (4) `offset_id` ranks 15/15 at 0.3-2.2% of leading-feature weight per symbol (1.1% portfolio) — the LightGBM did NOT learn offset-conditional structure, so the pooled-with-`offset_id` architecture DEGENERATES to a 3×-oversampled single-offset training, falsifying the multi-offset hypothesis as conceived. Critic FINAL `fa2090d` — single Critic round + one QR-response round (4 clarifications); all 8 checks evaluated; OVERALL=EXPLORATION-NEGATIVE; the candle-frequency axis (24h, 12h-2-offset, weekly-8-offset variants) is broadly CLOSED for cycle 6 by QR Round-2 + Critic concurrence.

**Date**: 2026-05-20
**Type**: EXPLORATION (cycle-6 slot #8 of 10; iter-v3/120 is the mandatory cycle-6 CONFIRMATION) — ran a full Phase 1–8 (EDA + brief + Phase-5.5 Engineer gate + backtest + Critic preliminary + QR response + Critic FINAL), classified at Phase 7.5.
**Verdict**: **EXPLORATION-NEGATIVE.** The 24h-multi-offset hypothesis (daily-frequency aggregation + 3× training-data multiplication via offset_id-aware pooled LightGBM lifts directional signal beyond the 8h representation) is FALSIFIED at production scale on the BCH/LDO/TRX cohort. The brief Section 4 explicit falsifier (OOS monthly Sharpe < −0.20 AND IS monthly Sharpe < +0.30) fires DECISIVELY on both axes (IS −2.17 << +0.30 with Δ −2.47 below the modal lower bound; OOS −3.26 << −0.20 with Δ −3.06 below the modal lower bound). The result falls BELOW the Section-7 Mode 4 Residual band's implicit lower bound (combining BCH portfolio-breaking loss + near-degenerate OOS trade count) — Mode 4 was sized at ~5% probability and the realized outcome over-shoots it.
**Decision**: **NO-MERGE.** BASELINE_V3.md UNCHANGED — canonical **`v0.v3-059`** (IS monthly Sharpe **+1.0894** / OOS monthly Sharpe **+0.5791**, 10-seed CONFIRMATION). An EXPLORATION never updates the baseline regardless of outcome; a catastrophic NEGATIVE EXPLORATION cannot advance to the iter-v3/120 CONFIRMATION bundle. `v0.v3-117` is a closeout marker only.
**Branch**: `iteration-v3/117`

---

## 1. Setup — the axis (brief reference)

iter-v3/117 advances to the CANDLE-FREQUENCY axis per the 2026-05-20 user directive (`feedback_v3_candle_frequency_unblocked.md`): the 8h-only constraint LIFTED from /117 onward; the QR may pick any frequency; BCH/LDO/TRX universe + LightGBM + <2h wall-clock LOCKED. The /116 closeout's recommended candidate — 24h base with 3-offset multi-offset derived-series (offsets {0, 8, 16} UTC) — was adopted.

**Brief reference**: `briefs-v3/iteration_v3-117/research_brief.md`, commit `bb713e6`. Hand-chosen design parameters declared per `feedback_v3_brief_parameter_provenance.md` Section 0:
- Candle frequency = 24h (= 1d). Rationale: cycle-6's six 8h NEGATIVEs (/110-/115) empirically re-confirmed the /109 terminal null is intrinsic to the 8h representation; /113's standalone 8 daily features cleared their permutation null at AUC 0.5275 (p=0.00) → direct prior evidence the daily representation carries signal the 8h grid cannot exploit.
- Number of offsets = 3 at {0, 8, 16} UTC. Rationale: the 8h base candle stream produces exactly 3 sub-bars per UTC day; aligning offsets to 8h sub-bar boundaries is the natural look-ahead-free derivation.
- Per-symbol pooled-offset training architecture (1 LightGBM/symbol, pooled across 3 offsets, `offset_id` as a categorical-style int64 feature). Rationale: pooled-offset architecture multiplies training data 3× per LightGBM (~4500 rows vs ~1500 standalone), closing the data-count gap vs the 8h baseline (~5500 rows); single Optuna fit surface per symbol-month.
- Label timeout = 7 daily bars (= 168h, calendar-time-equivalent to /059's 21×8h). Rationale: the EDA's T6 saved `T5/T6_BAR_COUNT_EQUIV_REJECTED.csv` shows the BAR-count-equivalent design (21 daily bars) collapses BCH to 99.13% positive labels; calendar-time-equivalent scaling restores /059's barrier-asymmetry geometry.

**Hypothesis (brief Section 1)**: aggregating the 8h candle stream into a 24h decision grid with the 3-offset multi-offset derived-series technique produces a feature→label representation that carries directional signal the 8h representation lacks, by virtue of (a) the daily-frequency representation aggregating-out 8h microstructure noise that the /109 terminal null is built on, and (b) the 3-offset derivation multiplying per-symbol training data 3× while preserving the lower-frequency dynamics — and this signal will transfer through production LightGBM walk-forward training to lift the universe-aggregate IS monthly Sharpe materially above the /060 anchor (+0.8325) with a positive OOS Sharpe Δ.

**Pre-registered Section 4 explicit falsifier**: *"if the production OOS monthly Sharpe falls below −0.20 AND the IS monthly Sharpe falls below +0.30, the hypothesis is rejected — the universe-pooled AUC lift did NOT translate to production signal at all, and the EDA's signal is an artifact of the held-out-AUC measurement scope (or the LightGBM cannot exploit the 24h representation in production despite the EDA's positive evidence)."*

**EDA backing (brief Section 2)**: committed at SHA `c64a5fc` (`analysis/iteration_v3-117/`, 10 result tables T1-T10) BEFORE the brief per `feedback_v3_axis_selection_quant_discipline.md` and the auditable temporal fence. T9 universe-pooled held-out AUC = **0.5823** (the strongest in v3 history; lifts +0.0934 vs /109 8h-stack null, +0.0808 vs /113 8h+daily, +0.0548 vs /113 daily-ONLY). g1 hard gate FAIL (per-symbol AUC at 0.4778/0.5201/0.5092, none clearing q95). g2 PASS (universe-pooled q95 clears). The EDA's formal verdict was NO-GO under per-symbol gates; the substantive read was PARTIAL-GO at the universe level. Per THE PRIME DIRECTIVE the brief proceeded with an honest modal prediction band reflecting both the universe-pooled positive evidence and the per-symbol risk.

---

## 2. Implementation — setup commits, engineering commit, tests

Sequenced setup chain (8 commits before backtest), then 1 engineering report commit:

| SHA | Type | Description |
|---|---|---|
| `c64a5fc` | analysis | 24h multi-offset gating EDA (10 tables T1-T10, including T6 BAR-count-equivalent REJECTED snapshot) |
| `bb713e6` | docs | research brief — 10 sections; Section 3.5 enumerates 8 implementation changes |
| `3010932` | docs | Phase 5.5 Engineer gate PASS (`phase5p5_gate.md`) |
| `6294606` | feat | 24h-3-offset derived-series + REVERT /116 no_confirm (the substantive code change — `src/crypto_trade/features_v3/multioffset_24h.py` 570 lines + runner changes + tests) |
| `551732c` | fix | accept str data_dir in `multioffset_24h.py` (Path/str TypeError, runtime bug discovered after Engineer gate) |
| `ae881cb` | fix | `_detect_interval` mapped `86_399_999ms` to "1d" instead of "24h" → `lookup_features` sought non-existent `BCHUSDT_1d_features.parquet` → returned empty → 0 training features, 0 trades. Fix: extend the interval map to recognize 24h alongside 1d. |
| `ac2c9f6` | fix | risk-gate features added to 24h pipeline + `risk_v3` integration test (the production code commit the backtest ran against) |
| `e3363ae` | docs | engineering report + backtest results (`reports-v3/iteration_v3-117/`) |
| `72e234a` | docs | QR response to Critic preliminary (4 clarifications) |
| `fa2090d` | docs | Critic FINAL review — EXPLORATION-NEGATIVE |

**Code summary (commit `ac2c9f6`)**:
- `src/crypto_trade/features_v3/multioffset_24h.py` (NEW, 570 lines): `aggregate_to_24h()` via `groupby("bar_open_time")`, per-offset feature isolation in `compute_features_24h()`, BTC cross-asset joins on matching-offset panels via `bar_close_time` exact-equality.
- `run_baseline_v3.py`: new `--bar-interval {8h, 24h}` CLI flag (default 8h preserves prior-iteration byte-identity); 24h branch reads `data/features_v3_24h/<SYM>_24h_multioffset_features.parquet`; sets `BacktestConfig.interval = "24h"`, `cooldown_candles = 2`, `feature_columns = V3_FEATURE_COLUMNS + ["offset_id"]` (15-element); `REQUIRED_GAP = 72 = (7+1)×3×3`; runner pre-flight accretion-guard verifies bar-interval-conditional `REQUIRED_GAP`.
- `src/crypto_trade/strategies/ml/lgbm.py`: `_INTERVAL_MINUTES` extended with `"24h": 1440` alias.
- Runner enforces /116 no_confirm REVERT at three independent surfaces (line 1941-1943 argument; line 2837-2851 pre-flight assertion; line 1108-1112 `_canonical_v059` accretion guard) — all PASS confirmed in `run.log` lines 3-38.
- `tests/test_multioffset_24h_aggregation.py` (NEW): 3 adversarial test cases (look-ahead-free assertion; per-offset feature isolation; trade-loop integrity at 24h).

**Wall-clock**: 0.64h (well under the 2h cycle-6 EXPLORATION cap). Hardware: WSL2 Linux x86_64.

**Sacred constants verified**: `OOS_CUTOFF_DATE = 2025-03-24` UNCHANGED, `training_months = 24` UNCHANGED (run.log lines 11-12).

---

## 3. Results — Phase 7 OOS evaluation (first look)

This is the QR's first look at the iter-v3/117 OOS reports. The headline is decisively catastrophic on both axes.

### 3.1 Headline metrics (`reports-v3/iteration_v3-117/comparison.csv`)

| Metric | In-Sample | Out-of-Sample | OOS/IS Ratio |
|---|---:|---:|---:|
| **monthly_sharpe** | **−2.1702** | **−3.2589** | 1.5016 |
| daily_sharpe | −5.8163 | −10.9748 | 1.8869 |
| max_drawdown | 4.9059% | 0.9269% | 0.1889 |
| profit_factor | 0.4657 | 0.2361 | 0.5071 |
| win_rate | 36.47% | 40.00% | 1.0968 |
| n_trades | 170 | **25** | 0.1471 |
| total_pnl | −4.3030% | −0.9303% | 0.2162 |
| monthly_calmar | −0.8771 | −1.0037 | 1.1443 |
| weighted_pnl_total | −4.3030% | −0.9303% | 0.2162 |
| dsr | 0.0000 | — | — |
| pbo | 0.0000 | — | — |
| psr | 0.0000 | — | — |
| n_trials | 315 | — | — |
| n_effective_trials | 22 | — | — |

vs the /060 EXPLORATION-mode anchor (IS +0.8325 / OOS +0.1403):
- **IS Δ = −3.0027** (catastrophic — far below the Criterion 1 NEGATIVE floor at −0.10; 30× margin of failure)
- **OOS Δ = −3.3992** (catastrophic — far below the Criterion 1b NEGATIVE floor at −0.20; 17× margin of failure)

CPCV `frac_positive_paths = 0.600` (above the 0.55 gate); CPCV path Sharpe q75 = +0.7742. Per-cell mean PBO = 0.0000 (100% of 128 cells at 0). Per `feedback_v3_dsr_mode_artifact.md`, the DSR=0.0/PSR=0.0/PBO=0.0 are EXPLORATION-mode structural artifacts and are informational only — NOT BLOCK-triggering for TYPE=EXPLORATION. The `frac_positive_paths=0.60` uses return-proxy paths (candle-level) and is not contradictory with the catastrophic trade-Sharpe: the return-proxy reflects the underlying candle return distribution; IS/OOS trade Sharpe reflects the filtered, gated, confidence-thresholded SUBSET — the population-vs-tail divergence is the core diagnostic finding (Section 4 Mechanism 1).

### 3.2 Per-symbol attribution (`reports-v3/iteration_v3-117/in_sample/per_symbol.csv` + `comparison.csv`)

**IS per-symbol:**

| Symbol | Trades | Win Rate | Net PnL | Avg PnL/trade | pct_of_total_pnl |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 67 | 47.8% | −4.6491% | −0.0694% | 53.49% |
| LDOUSDT | 24 | 66.7% | +0.8665% | +0.0361% | −9.97% |
| TRXUSDT | 79 | 24.1% | −4.9095% | −0.0621% | 56.48% |

**OOS per-symbol:**

| Symbol | Trades | Win Rate | Net PnL | concentration_pct |
|---|---:|---:|---:|---:|
| BCHUSDT | 11 | 27.3% | −0.8767% | **58.18%** |
| LDOUSDT | 14 | 50.0% | −0.7199% | **41.82%** |
| TRXUSDT | **0** | — | — | — |

**Attribution finding**: all three OOS symbols are catastrophically negative or absent. **TRX produced ZERO OOS trades despite 79 IS trades** (verified by `grep -c TRXUSDT reports-v3/iteration_v3-117/out_of_sample/trades.csv = 0`). BCH leads OOS concentration at 58.18% with WR=27.3% (below the 33.3% 2:1 ATR breakeven). LDO is at 41.82% with WR=50.0% (above breakeven but insufficient to offset fees). No single symbol carries the portfolio. OOS months with any trades: 6 of 14 (2025-07/08/09/10, 2026-04/05); zero-trade months: 8 of 14 (2025-04/05/06/11/12, 2026-01/02/03). 1.79 OOS trades/month is far below the v3 trade-rate floor (≥10/month).

---

## 4. Critic Review Summary (Phase 7.5)

Critic FINAL at commit `fa2090d` — single Critic preliminary round + one QR response round (4 clarifications); all 8 checks evaluated.

### 4.1 Per-Check status

| # | Check | Status | Diagnostic |
|---|---|---|---|
| 1 | Look-Ahead Audit | **PASS** | `multioffset_24h.py` is causally clean; aggregation, per-offset feature isolation, BTC cross-asset joins on `bar_close_time` exact-equality, past-only ATR labeling. EDA T4 audit 900/900 PASS + QE Change-8 adversarial integration test (3 sub-tests) validate. |
| 2 | Embargo Width | **FAIL** | Panel-level `REQUIRED_GAP = 72` correctly sizes the global CPCV embargo; the walk-forward train-end-time embargo at `walk_forward.py:91-113` (8 daily bars = 8 calendar days) is sufficient at the WITHIN-OFFSET level. **HOWEVER** the inner Optuna CV gap at `lgbm.py:494-498` is NOT panel-aware: `cv_gap = embargo_candles × n_symbols = 8 × 1 = 8 rows = 2.67 daily bars`, but the 24h-multi-offset panel has 3 rows per calendar day; within each per-symbol Optuna CV fold, the last ~13 rows of the training fold have forward-label deadlines reaching ~4.33 daily bars into the validation fold. QR conceded the brief Section 5 Risk 2 prose described intended behavior, not implemented behavior — `n_offset_series` is invisible to `LightGbmStrategy` because offset interleaving happens at the data-load layer. **Impact**: IS metrics biased upward by within-fold cross-offset label leakage; does NOT by itself explain OOS collapse (driven by Mechanisms 1-3 + refined Mechanism 4). **Code defect filed: ONLY-IF /118 uses multi-offset architecture, thread `n_offset_series` parameter into `LightGbmStrategy.__init__` (default 1) and multiply at `lgbm.py:498`.** |
| 3 | Multiple-Testing Correction | **FAIL (informational for EXPLORATION)** | DSR=0.0 / PBO=0.0 / PSR=0.0 — EXPLORATION-mode structural artifacts per `feedback_v3_dsr_mode_artifact.md`. `frac_positive_paths=0.60` is above the 0.55 gate. PBO=0 at 100% of cells with catastrophic Sharpe collapse is structurally consistent with an unviable hypothesis. Informational only — does not BLOCK for TYPE=EXPLORATION. |
| 4 | IC Correlation | **WARN** | `ic_matrix.csv` is 14×14 — runner-appended `offset_id` (15th feature) is NOT in the matrix. QR conceded one-line documentation defect: writer iterates `V3_FEATURE_COLUMNS` instead of runtime `_feature_columns`. Methodology-level inert because `offset_id` has only 3 discrete values {0, 8, 16} (continuous-IC bounded by ≈ ±0.2 by variance-partition argument) AND LightGBM importance rank 15/15 at ~1% of leading weight independently establishes non-load-bearing status. Documentation defect, not blocker. |
| 5 | ADF Stationarity | **PASS** | Runner-level 1803/2198 stationary (82.0%); EDA-level T7 17/42 (40.5%) at IS-end snapshot reflects 24h warm-up artifact (200-bar lookbacks need ~200 calendar days to stabilize). `min_periods` enforcement excludes warm-up rows from training. The 40.5% EDA / 82.0% runner gap is the expected 24h warm-up-attenuation. |
| 6 | Pareto Dominance | **N/A** | EXPLORATION mode uses `ENSEMBLE_SIZE=3` inner seeds with NO outer-seed loop per `feedback_v3_outer_seed_cap_2_v3.md`. Architecturally correct. |
| 7 | Reproducibility | **PASS** | Commit SHA `ac2c9f6` stamped; `feature_columns` explicit at 15 (runner constructs `_feature_columns = V3_FEATURE_COLUMNS + ["offset_id"]`); ensemble seeds literal in `ENSEMBLE_SEEDS` (191664963, 1662057957, 1405681631); all 16 accretion-guard knobs PASS at runner pre-flight; trade-arithmetic spot-checks of OOS trades 1, 2, 7 verify 2:1 ATR barrier geometry. |
| 8 | Hypothesis-Implementation Alignment | **PASS** | All 8 brief Section 3.5 changes implemented and verified at source. The hypothesis was correctly implemented; the hypothesis failed empirically. |

### 4.2 OVERALL line

OVERALL: **EXPLORATION-NEGATIVE** — Section 8 Criterion 1 (NEGATIVE) fires decisively on BOTH arms (IS −2.17 << +0.7325 floor; OOS −3.26 << −0.0597 floor); the pre-registered explicit falsifier ("OOS < −0.20 AND IS < +0.30") fires on both axes; the 24h-multi-offset hypothesis is FALSIFIED at production scale; the worst /117 result in cycle-6 history.

### 4.3 Mechanism 4 refinement (Critic-corrected, QR-accepted Round 2)

The engineering report's prose ("z-score gate calibrated on 8h IS statistics") is mechanically incorrect. QR audited `risk_v2.py:533-545`: the per-symbol z-score gate parameters (`feature_mean[symbol]`, `feature_std[symbol]`) are REBUILT at every training-month boundary from the current IS slice — there is no carried-over 8h calibration. The empirically real LDO 69.5% over-fire has a different mechanism:

(a) **Pooled-across-3-offsets mean/std**: the 3 offsets (0h, 8h, 16h UTC) have heterogeneous feature distributions (funding-cycle-aligned vs mid-cycle vs post-cycle). Pooling produces a per-symbol std that is wider than any single offset's std (between-offset variance + within-offset variance compounded into total variance). Offset-0 features evaluated against the pooled mean/std exhibit inflated z-scores. LDO's 24h aggregation has the highest between-offset heterogeneity in the 3-symbol universe.

(b) **LDO small-sample std estimation**: LDO has ~707 rows per offset (T2 row counts) vs 8h's ~2120 contiguous rows. Noisier std at small per-offset sample size, amplified by 3-offset pooling → more z-score tail mass over the z=2.0 threshold → higher gate-kill rate.

(c) **z=2.0 fixed threshold inappropriate for the pooled-multi-offset distribution**: the /059-canonical z=2.0 was IS-calibrated on 8h single-series tail shapes. The 24h-multi-offset pooled distribution has heavier tails (between-offset variance + within-offset variance compounded), so z=2.0 captures more mass than intended.

**The over-fire is intrinsic to the multi-offset architecture — NOT a separable threshold-recalibration knob.** This strengthens — not weakens — the FALSIFIED verdict because the over-fire is structurally induced by the 3-offset pool.

---

## 5. Failure-Mode Analysis — the 4-mechanism trace

The catastrophic outcome decomposes into 4 mechanisms, in roughly causal order (Critic-refined Round 2).

### 5.1 Mechanism 1 — AUC vs gated-tail (population-vs-tail divergence)

EDA universe-pooled held-out AUC = **0.5823** (v3's strongest ever). Production IS monthly Sharpe = **−2.1702**. Not contradictory — they measure different objects.

AUC 0.5823 means the model rank-orders `predict_proba` slightly better than random across the FULL population of 12,280 IS rows. But the confidence gate (realized threshold 0.648 for BCH) selects only the HIGH-CONFIDENCE tail. The key question is whether the high-confidence tail is directionally correct. Per-symbol IS WR vs the 2:1 ATR breakeven (33.3%):
- BCH 47.8% (above raw breakeven, but fee-dominated at avg PnL −0.0694%/trade → 0.478×(2×ATR) − 0.522×ATR − 0.10% fee net to ≈ −0.035%/trade at ATR=0.15%).
- TRX 24.1% — **BELOW 33.3% breakeven**. High-confidence TRX predictions are systematically wrong — the population-vs-tail divergence is the primary mechanism.
- LDO 66.7% — above breakeven, but 24 trades insufficient to carry portfolio.

The population AUC of 0.5823 captures rank-ordering across the FULL panel including the 0.88% SL-hitting rows (label=0). A model that outputs near-1.0 for most rows can have AUC > 0.5 on a 99% positive panel if the rare negative rows happen to be ranked lower. **The AUC is a high-imbalance artifact, not a discriminative-quality signal.**

### 5.2 Mechanism 2 — BCH 99.12% label imbalance

BCH labels at 24h are 99.12% positive (TP hits) on the /059-faithful (atr_tp=2.0, atr_sl=1.0, calendar-time-equivalent timeout=7 daily bars). The +2 ATR target almost always hits before the −1 ATR stop on BCH at the daily-frequency scale — a structural property of BCH's 24h volatility profile on the BCH/LDO/TRX cohort, not a labelling bug. The brief's Section 2.3 documented this explicitly (T6 label balance: BCH p(label=1)=0.9912, LDO 0.6451, TRX 0.5665).

A LightGBM trained on this panel cannot learn from SL-hitting events (only 0.88% of training rows). The resulting model likely produces `predict_proba` values consistently near-1.0 for LONG bets regardless of whether the current market state is trending or mean-reverting. The confidence gate at 0.648 selects what appear to be "high-confidence" LONG predictions, but they are not informative because the model has no SL-class signal to calibrate against.

The brief's Risk 1 mitigation (the 7-gate RiskV2 stack filters by mechanism orthogonal to the LightGBM signal) partially worked — BCH's IS trade book stayed at 67 trades, not 627 (the kill rate was 67.8%) — but the admitted-trade book was still fee-dominated at 47.8% WR.

### 5.3 Mechanism 3 — TRX 79 IS → 0 OOS evaporation (IS-overfit-to-noise)

TRX generated 79 IS trades at WR=24.1% — producing IS net PnL of −4.9095%, the largest IS loss driver. In OOS it generated ZERO trades. The TRX model learned some IS-specific pattern that (a) fired frequently IS and (b) was directionally wrong (24.1% WR << 33.3% breakeven), then (c) produced no OOS signal at all. **This is the hallmark of IS-specific overfitting on a noisy target**: the model found false IS regularities that don't transfer OOS. The 24h-multi-offset TRX panel (3× sample size relative to single-offset) gave LightGBM more rows on which to find spurious IS regularity.

Verified: `grep -c TRXUSDT reports-v3/iteration_v3-117/out_of_sample/trades.csv = 0`.

### 5.4 Mechanism 4 — Pooled-multi-offset z-score gate over-fire (Critic-refined)

LDO 69.5% z-score kill rate is structurally induced by the multi-offset architecture as documented in Section 4.3 above. The brief's Section 5 Risk 2 documented an INTENDED panel-aware behavior; the IMPLEMENTED inner Optuna CV gap is panel-unaware (Critic Check 2 FAIL). The kill-rate over-fire is intrinsic to the 3-offset pool; not a separable knob.

### 5.5 Offset_id rank 15/15 — the falsifying observation

The model importance tables (`reports-v3/iteration_v3-117/in_sample/model_importance_last_month_*.csv`) show `offset_id` ranks LAST in every symbol and the portfolio aggregate:

| Symbol | offset_id importance | Total importance sum | offset_id share | Rank |
|---|---:|---:|---:|---|
| BCHUSDT | 1.0 | 300.3 | **0.3%** | 15/15 |
| LDOUSDT | 8.3 | 1146.3 | **0.7%** | 15/15 |
| TRXUSDT | 11.7 | 533.5 | **2.2%** | 15/15 |
| Portfolio | 21.0 | 1980.4 | **1.1%** | 15/15 |

**The model effectively did NOT learn to distinguish offsets.** The QR's brief Section 3.5 explicitly framed `offset_id` as the mechanism by which LightGBM would learn offset-specific signal structure ("if the model learns offset-conditional patterns, `offset_id` will rank in the top 5 features"). At rank 15/15 with importance ~1% of leading weight, **LightGBM did NOT learn offset-conditional structure** — the 3-offset architecture DEGENERATES to a 3×-oversampled single-offset training, which was the architecture's worst-case failure mode (per the EDA's PARTIAL-GO caveat).

The brief Section 2.4 T3 per-offset breakdown showed heterogeneous per-offset AUC (BCH strongest at offset 0 = 0.6213; LDO strongest at offset 0 = 0.5485; TRX strongest at offset 16 = 0.5455), so the per-offset structural information was present in the data — but the LightGBM found `offset_id` uninformative AS A FEATURE. The hypothesis as conceived (LightGBM learns offset-conditional patterns) is falsified by the 0.3–2.2% importance.

---

## 6. Closure Scope — the candle-frequency axis is broadly CLOSED for cycle 6

Per QR Round-2 Clarification 4 + Critic concurrence (`fa2090d` line 16):

**The candle-frequency axis (24h, 12h-2-offset, weekly-8-offset variants) is broadly CLOSED for cycle 6.** The /116 diary Section 9 Mode 4 RESIDUAL fallbacks (12h-2-offset, weekly-8-offset) are de-prioritized because the three confounders all RECUR at any multi-offset cadence on the BCH/LDO/TRX cohort:

(a) **BCH 99.12% label imbalance**: a property of BCH's volatility distribution at the 24h+ scale paired with the /059-canonical (2.0, 1.0) ATR multipliers and 7-daily-bar timeout. Tightening barriers at 12h or 1d-weekly would shift but not eliminate the imbalance — the underlying universe was selected on 8h volatility profiles, and the alt-cohort's 24h+ volatility is structurally low-amplitude. Any candle-frequency axis at 12h or longer faces a related imbalance problem on BCH or TRX.

(b) **Pooled-multi-offset z-score gate over-fire**: structurally induced by ANY multi-offset architecture (2-offset, 3-offset, 8-offset). The gate-calibration code rebuilds per-symbol mean/std from the pooled IS distribution; pooling across heterogeneous offsets inflates std regardless of how many offsets. Re-calibrating z=2.0 → z=2.5 would lift the tail mass cutoff but introduces a data-snooped axis-tuning knob that wasn't pre-registered — a `feedback_no_cheating.md` violation if attempted at /118.

(c) **offset_id rank 15/15**: the falsifying observation for the multi-offset hypothesis as conceived. The multi-offset design was the BEST CASE for the candle-frequency hypothesis because it gave LightGBM the maximum information about the daily-frequency representation while preserving 3× training-data density. The fact that LightGBM weighted offset_id at 1% of the leading feature's importance means daily-frequency aggregation provides no separable signal lift even when handed to the model on a platter. A single-offset 24h design would have strictly LESS information and strictly LESS training density — the architecture's failure mode is not addressable by stripping the multi-offset layer; it's a property of the daily-frequency representation itself on the BCH/LDO/TRX universe.

The Mode 4 RESIDUAL fallback paths were predicated on /117 filing as BEHAVIORAL-INERTIA (≤ 30 IS trades). /117 filed Mode 1 substantive NEGATIVE (170 IS trades, IS −2.17, OOS −3.26 in the operative regime), NOT Mode 4 — the fallback activation condition did NOT fire.

**Future re-opening of the candle-frequency axis requires either**:
(i) a DIFFERENT 3-symbol universe with favorable 24h volatility profiles (the cycle-6 universe-selection axis was CLOSED at /110/111 NEGATIVEs — re-opening requires a new structural argument), or
(ii) a STRUCTURALLY DIFFERENT multi-offset architecture (per-offset separate models + late-fusion, NOT pooled-with-`offset_id` training) — a new candidate for future cycles.

Neither is a cycle-6 axis. The candle-frequency axis is filed as a cycle-6 dead path.

---

## 7. Catalog entry

Per Critic Recommendation 4 + the standard schema, appended to `briefs-v3/exploration_catalog.md`:

```
| iter-v3/117 | 2026-05-20 | candle frequency 8h → 24h-multi-offset | −2.97 | −3.40 | EXPLORATION-NEGATIVE | NO |
```

Cycle-6 catalog state (after /117):
- 7 NEGATIVE: /110 (label-confound), /111 (clean), /112 (pooled architecture), /113 (multi-frequency on 8h), /114 (risk management with Check-1 FAIL), /115 (coherent horizon-exit labeling), /117 (24h-multi-offset)
- 1 PROMISING-MECHANICAL: /116 (no_confirm early-exit primitive — strictly-accretive component decision for the /120 CONFIRMATION bundle)
- 2 EXPLORATION slots remaining: /118, /119
- /120 = mandatory cycle-6 CONFIRMATION

**Code defect filed (Critic Check 2 FAIL, conditional)**: ONLY-IF any future iteration uses multi-offset architecture, thread an `n_offset_series` parameter (default 1) into `LightGbmStrategy.__init__`, pass it from `run_baseline_v3.py` when `--bar-interval 24h`, and multiply at `lgbm.py:498`: `cv_gap = embargo_candles * n_symbols * n_offset_series`. ALSO one-line fix at the IC-matrix writer: iterate `_feature_columns` (runtime list) not `V3_FEATURE_COLUMNS`. Both fixes are NOT REQUIRED at /118 if /118 stays at single-frequency 8h.

---

## 8. Next Iteration Ideas — /118 axis recommendation

Cycle 6 has 2 EXPLORATION slots remaining (/118, /119) before the mandatory /120 CONFIRMATION. Cycle-6 axis menu state after /117:

| Cycle-6 axis | Status |
|---|---|
| Universe / symbol selection | CLOSED at /110 (label-confound) + /111 (clean NEGATIVE — wholesale 4-symbol replacement CRV/AAVE/GRT/ADA) |
| Pooled-vs-per-symbol model architecture | CLOSED at /112 NEGATIVE |
| Multi-frequency features on 8h decision grid | CLOSED at /113 NEGATIVE |
| Risk management primitives | CLOSED at /114 NEGATIVE |
| Labeling architecture (coherent horizon-exit) | CLOSED at /115 NEGATIVE; also /072 (incoherent) + /108 (meta-labeling) + /017 (meta-labeling) |
| Trade-construction / exit-layer primitive | PROMISING-MECHANICAL at /116 (no_confirm) — bundled at /120 |
| **Candle frequency (24h-multi-offset, 12h-2-offset, weekly-8-offset)** | **CLOSED at /117** (this iteration) |
| NEW engineered feature family at 8h | **LIVE** (regime_momentum_signed_5d lineage proven at /025 PROMISING; never re-explored as a structural axis since) |
| Per-symbol model architecture (XGBoost-with-categorical-handling) | **LIVE** (the iter-v3/016 LightGBM→XGBoost closure was at universal-cohort + cross-entropy + depth-wise defaults; per-symbol + imbalance-aware configurations NOT closed) |

### 8.1 The /118 recommendation: out-of-the-box

The Critic offered two candidates:
- **(a)** NEW engineered feature family at 8h on the regime_momentum_signed_5d lineage (composed features per `feedback_v3_engineered_features_proven.md`)
- **(b)** Per-symbol XGBoost-with-categorical-handling for BCH's imbalanced cell

Both are defensible. The orchestrator's autopilot directive is QR-led EDA discipline per `feedback_v3_axis_selection_quant_discipline.md` — the next QR makes the call from a committed EDA.

**My recommendation — out-of-the-box, between (a), (b), and a new alternative — is candidate (a) NEW engineered feature family at 8h, BUT structured differently than the Critic's framing.**

The narrative reason: the Critic's (b) (per-symbol XGBoost-with-categorical-handling for BCH) targets BCH's 24h-imbalance failure mode at the model-architecture layer. But the 24h-imbalance is a property of BCH's daily-frequency volatility profile (Mechanism 2 above) — NOT a structural property of LightGBM. At the 8h baseline, BCH's label imbalance is materially less severe (the /059-canonical labels at 8h show BCH p(label=1) ≈ 0.59-0.64, not 0.99). **XGBoost-with-categorical-handling targets a problem that doesn't manifest at 8h.** The /016 closure was at universal-cohort + cross-entropy + depth-wise defaults; per-symbol + imbalance-aware configurations remain LIVE, but the imbalance the architecture would address is the 24h-imbalance the QR has just closed. Running (b) at 8h would address a problem the 8h baseline does not have at the magnitude (b)'s configurations are designed for.

The structural reason: cycle 6's catalog is 7 NEGATIVE + 1 PROMISING-MECHANICAL. The PROMISING came from a TRADE-CONSTRUCTION / EXIT-LAYER axis (/116 no_confirm), NOT a feature or model-architecture axis. Per `feedback_v3_structural_over_knob_exploration.md`, structural axes outrank knob axes; per `feedback_v3_engineered_features_proven.md`, ENGINEERED features OUTPERFORM off-the-shelf indicators (iter-v3/025 first PROMISING in post-bootstrap; importance 51% top vs 22-25% for off-the-shelf NEW features). The engineered-feature lineage has a proven empirical track record in v3 that no other live axis has matched. Cycle 6 has not tried a NEW engineered feature; the closest precedent (/113) was a multi-frequency feature on an 8h grid, NOT a composed engineered feature.

**Out-of-the-box framing — what makes /118 different from the saturated patterns**:

Past v3 NEW-feature EXPLORATIONs (iter-v3/015 tbr_zscore_30, iter-v3/019 funding_rate_zscore_30, iter-v3/023 funding retest at n=35, iter-v3/024 btc_funding_rate_zscore_30, iter-v3/053 hurst_drift_50_200, /054 onwards) have a near-universal failure pattern: the feature ranks 14/14 (or 15/15) in LightGBM importance and the model "doesn't learn it" — the Linear-Redundancy-Pre-Falsifier methodology (`feedback_v3_lr_pf_methodology.md`) and the composed-feature carve-out (`feedback_v3_engineered_feature_pivot.md`) are the cycle's accumulated discipline.

But /025's `regime_momentum_signed_5d = ret_5d × sign(hurst_100 − 0.5)` HAS the engineered structure that worked. The orthogonal question /118 should ask is: **what is the next composed feature in that lineage that is (i) explicitly mechanistically motivated by a v3 cycle-6 failure mode and (ii) NOT redundant with existing v3 features by the Linear-Redundancy Pre-Falsifier?**

A specific proposal — NOT a pre-commitment, the /118 QR adjudicates — is a **regime-conditioned mean-reversion vs trend composite** of the form:

```
composite_X = (zscore_20d × sign(hurst_100 − 0.5)) × adx_norm_14d
```

(or similar — the exact form is the QR's adjudication). The structural argument:

- The /116 no_confirm primitive's slot-freeing cascade exploits a regime-asymmetry the v3 features don't currently encode at the feature level — the regime where a trade should NOT confirm is implicit in the no_confirm primitive's gate-rule but not exposed as a feature for the LightGBM to learn from. A composed feature encoding "I am in a low-momentum regime where mean-reversion dominates" gives the LightGBM a direct signal for the same regime structure that /116's cascade is currently exploiting at the exit layer.
- The composed structure (multiplied by `sign()` to flip in different regimes) is exactly the /025 PROMISING-feature pattern — non-redundant with the V3_FEATURE_COLUMNS primitives by construction (the Critic's L-R PF carve-out applies).
- It's a NEW engineered feature, NOT a new architecture, NOT a new universe, NOT a new gate threshold — it stays in the LIVE structural-axis subset.

The /118 QR may choose a DIFFERENT composed feature (e.g. a volatility-of-volatility composite; a cross-asset BTC-correlation × regime composite; an OBV-based composite) — the recommendation is the AXIS (NEW engineered feature at 8h), not the specific feature.

### 8.2 EDA seed for /118 — what IS-only analysis script the next QR should commit BEFORE the brief

Per `feedback_v3_axis_selection_quant_discipline.md`, the /118 QR must commit a QR-led EDA in `analysis/iteration_v3-118/*.py` BEFORE writing the brief. The EDA seed (a starting point, not a complete spec):

**`analysis/iteration_v3-118/engineered_feature_screen.py`** — an IS-only script that:

1. **Catalogs the v3 cycle-6 failure modes that engineered features could plausibly address.** Reads `analysis/iteration_v3-115/`, `/116/`, `/117/` EDA tables and isolates the regime-conditioned signal patterns (e.g., the /116 EDA T8 held-to-barrier counterfactual showed regime-dependent slow-start trades; the /117 EDA T3 per-offset breakdown showed regime-dependent per-offset AUC heterogeneity; the /115 EDA T4 IC ratio showed horizon-exit-label has ~1.5× IC than triple-barrier). Lists 4–6 candidate composite-feature forms motivated by these patterns.

2. **For each candidate, runs the Linear-Redundancy Pre-Falsifier on V3_FEATURE_COLUMNS.** Computes the candidate's R² on a linear regression against the existing 14 features (per `feedback_v3_lr_pf_methodology.md`). REJECT if R² > 0.50 AND not a composed-feature with algebraic-identity carve-out (per `feedback_v3_engineered_feature_pivot.md`). PASS-list ≥ 3 candidates for the next step.

3. **For each PASS-list candidate, runs the walk-forward feature→label predictive screen** (the /109 / /117 / /110 methodology — per-fold OOF AUC, universe-pooled across the 3 symbols, with the permutation null). Choose the candidate with the HIGHEST observed AUC AND p-value < 0.05.

4. **For the chosen candidate, computes per-symbol AUC** (the /117 g1 hard gate) AND the importance-rank prediction for a depth-3-5 LightGBM (the /025 PROMISING benchmark: ≥ rank 5/15, importance ≥ 30% of top-feature). If the candidate fails per-symbol AUC AND fails the importance-rank prediction, flag it as PROMISING-INERT-RISK in the brief Section 7.

5. **Commits 6+ result tables (T1-T6 minimum) + a synthesis.md before writing the /118 brief.**

The /118 QR may extend the EDA further (e.g., stationarity audit on the candidate, cross-asset audit, regime-stability audit across the 3-symbol panel), but the 5-step skeleton above is the minimum to satisfy `feedback_v3_axis_selection_quant_discipline.md` for an engineered-feature axis.

### 8.3 Why NOT candidate (b) at /118

For completeness — XGBoost-with-categorical-handling per-symbol-for-BCH is a defensible cycle-6 axis but its claim ground is the 24h-imbalance failure mode the QR has just closed. At 8h the imbalance manifests at a different magnitude (BCH p(label=1) ≈ 0.59-0.64, not 0.99); the configurations XGBoost-with-categorical-handling brings (categorical-aware tree splitting; class-weighted loss; focal loss) target the 99%-imbalance use case more than the 64%-imbalance one. If a future iteration re-opens the 24h axis on a different universe (per the /117 closure-scope future-re-opening conditions), candidate (b) MAY become the natural model-architecture choice. At /118 with the 8h baseline, the marginal value-add over LightGBM is smaller. Defer to a future cycle.

### 8.4 Cycle-6 trajectory

After /118 EDA + brief + backtest + Critic, /119 is the final EXPLORATION slot. The recommendation for /119 (subject to /118 outcome) is the second-priority LIVE structural axis — either a second NEW engineered feature (if /118 PROMISING) or candidate (b) XGBoost-with-categorical-handling per-symbol at 8h (if /118 NEGATIVE and the QR wants the model-architecture sanity check before /120). The /120 CONFIRMATION bundles the /116 no_confirm primitive as strictly-accretive per `feedback_promising_mechanical_subtype.md` Recommendations 1-3.

---

## 9. Closeout

- **Verdict**: EXPLORATION-NEGATIVE — the 24h-multi-offset hypothesis is FALSIFIED at production scale on the BCH/LDO/TRX cohort.
- **Mechanisms (Critic-refined)**: (1) population-vs-tail divergence (high-imbalance AUC artifact); (2) BCH 99.12% label imbalance → near-degenerate `predict_proba`; (3) TRX 79 IS → 0 OOS evaporation (IS-overfit-to-noise); (4) pooled-multi-offset z-score gate over-fire (structurally induced, not a separable knob). The falsifying observation is `offset_id` rank 15/15 at ~1% importance — LightGBM did NOT learn offset-conditional structure.
- **Closure scope**: candle-frequency axis (24h, 12h-2-offset, weekly-8-offset) broadly CLOSED for cycle 6 per QR Round-2 + Critic concurrence.
- **Code defect filed**: panel-aware inner Optuna CV gap (`lgbm.py:498`) + IC-matrix writer iterating `_feature_columns` — conditional on /118+ using multi-offset architecture.
- **Decision**: NO-MERGE. BASELINE_V3.md UNCHANGED at `v0.v3-059`. Catalog updated. `v0.v3-117` tagged as closeout marker only.
- **/118 axis recommendation**: NEW engineered feature family at 8h on the regime_momentum_signed_5d lineage (candidate (a) preferred over (b) XGBoost-with-categorical-handling for the imbalance-magnitude argument above). EDA seed: `analysis/iteration_v3-118/engineered_feature_screen.py` per the 5-step skeleton above.
- **Cycle 6 state**: 7 NEGATIVE / 1 PROMISING-MECHANICAL / 2 EXPLORATION slots remaining (/118, /119) / 1 CONFIRMATION (/120).

See `briefs-v3/iteration_v3-117/research_brief.md`, `briefs-v3/iteration_v3-117/engineering_report.md`, `briefs-v3/iteration_v3-117/review_preliminary.md`, `briefs-v3/iteration_v3-117/qr_response.md`, `briefs-v3/iteration_v3-117/review.md`, `reports-v3/iteration_v3-117/`, and `briefs-v3/exploration_catalog.md` for full artifacts.
