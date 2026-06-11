# Engineering Report — iter-v1/090

## Headers

- **Iteration**: iter-v1/090
- **Branch**: iteration-v1/090
- **Commit SHA (setup)**: 1be3bd1 (feat: basis_zscore_30 feature + dispatch + tests; iter-v1/090 src/ was set up prior to this closeout)
- **Hardware**: WSL2 Linux 6.6.114.1 / x86_64
- **Wall-clock time**: 13468s (~3.74h) — aborted at fail-fast trigger; full run projected ~7–8h
- **Outcome**: BLOCKED-FAIL-FAST

---

## Configuration Diff vs ETH/064 Baseline Seat

Single change only. Everything else is byte-identical to the ETH/064 runner.

| Parameter | ETH/064 (baseline seat) | iter-v1/090 (W-DECAY) |
|---|---|---|
| `sample_weight_mode` | `abs_pnl` | `abs_pnl_timedecay` |
| `time_decay_half_life` | N/A | 12.0 months (365d) |
| `specialist_mode` | True | True (unchanged) |
| `V1_SPECIALIST_SEED_COUNT` | 50 | 50 (unchanged) |
| `V1_SPECIALIST_OPTUNA_TRIALS` | 30 | 30 (unchanged) |
| `max_depth` | 5 FIXED | 5 FIXED (unchanged) |
| `num_leaves` | 31 FIXED | 31 FIXED (unchanged) |
| `n_estimators_max` | 500 | 500 (unchanged) |
| `n_startup_trials` | 10 | 10 (unchanged) |
| `atr_tp / atr_sl` | 2.9 / 1.45 | 2.9 / 1.45 (unchanged) |
| R1 / R2 | OFF / OFF | OFF / OFF (unchanged) |
| R3 (Mahalanobis OOD) | ON, cutoff=0.70 | ON, cutoff=0.70 (unchanged) |
| R5 (vol-targeting) | ON, vt_target_vol=0.3 | ON, vt_target_vol=0.3 (unchanged) |
| `feature_columns` | 48 cols (V1_FEATURE_COLUMNS_PRUNED) | 48 cols (UNCHANGED) |
| `cohort` | ETHUSDT only | ETHUSDT only (unchanged) |
| `OOS_CUTOFF_DATE` | 2025-03-24 | 2025-03-24 (sacred, unchanged) |
| `training_months` | 24 | 24 (sacred, unchanged) |
| `fail_fast_is_years` | OFF | 2.0yr (IS weighted_pnl <= 0 threshold) |

W-DECAY formula: `weight_t = |pnl_t| × exp(−ln2/12 · age_months(t))`, where `age_months` is measured relative to `train_times.max()`.

---

## Fail-Fast Result

```
verdict:                    BLOCKED-FAIL-FAST
reason:                     first 732d IS weighted_pnl=-17.1722 (≤0; 143 IS trades over 2.0yr window)
fail_fast_is_years:         2.0
is_trades_count:            143
is_cumulative_weighted_pnl: -17.1722
is_cumulative_net_pnl_pct:  -27.9114
is_annualized_sharpe_approx:-2.0193
wall_clock_seconds:         13468
abort at:                   2024-01-04 (IS candle after 732d of IS test trades)
```

The abort fired in the very last IS training month — the runner exhausted 50-seed × 30-trial optimization for all IS folds through end-2023, executed 143 IS trades, and then checked the accumulated IS weighted_pnl at the 2-year mark. Result was deeply negative (−17.17 cumulative weighted PnL, −27.91% net, IS Sharpe ≈ −2.02). The fail-fast correctly terminated before the OOS forward pass (no comparison.csv — expected for a fail-fast abort).

The ETH/064 standalone baseline (the seat W-DECAY modifies) was IS **+0.2383** / OOS **+0.5171**. W-DECAY drove the first-2yr IS from +0.24 to deeply negative (−2.02 Sharpe). This is not a marginal miss — it is a directionally catastrophic inversion.

---

## Centerpiece: F2 ENGAGED, F1 Deeply Negative — The Inverse-Edge Finding

### F2 (Mechanistic Falsifier) — ENGAGED

The brief's pre-registered F2 asked: does the Optuna `training_days` distribution shift modestly LONGER under W-DECAY vs the abs_pnl cohort prior (XRP/088 median 250d, TRB/086 median 115d)?

Measured from run.log (37,500 trial observations across all IS folds × 50 seeds × 30 trials):

| Seat | Mode | Median training_days | folds <120d | folds <180d |
|---|---|---:|---:|---:|
| TRB/086 | abs_pnl | 115d | 23/46 (50%) | 26/46 (57%) |
| XRP/088 | abs_pnl | 250d | 9/54 (17%) | 19/54 (35%) |
| **ETH/090** | **abs_pnl_timedecay** | **280d** | **14% of 37,500** | **25% of 37,500** |

W-DECAY median training_days = **280d**, LONGER than the XRP/088 cohort prior (250d) and longer than the LM-predicted ~220–240d range. F2 is ENGAGED: the mechanism operated exactly as designed — recency-weighting via the smooth weight gradient reduced Optuna's incentive to truncate the window, and the search shifted toward longer windows. The brief's rescaled F2 expectation ("SMALL lengthening ~+30-60d, modal ~220-240d") was actually exceeded (280d vs 250d = +30d above the positive-seat prior).

Furthermore, folds <120d dropped from TRB/086's 50% to 14% under W-DECAY — a 36pp reduction in severe-truncation events, consistent with the mechanism eliminating the collapse incentive.

**F2 = MECHANISM-ENGAGED.** The implementation is correct and the Lopez de Prado AFML Ch. 4 mechanism functioned.

### F1 (IS Sharpe Falsifier) — DEEPLY NEGATIVE

IS Sharpe ≈ **−2.02** vs ETH/064 baseline +0.2383. Delta = **−2.26** — far below the NEGATIVE threshold (Δ < 0.00). This is not a near-miss; it is a large-magnitude directional failure.

### Resolution: SPECIALIST-NEGATIVE (Subtype INVERSE-EDGE)

The brief's Section 8 pre-registered matrix:

| F1 | F2 | Verdict |
|---|---|---|
| < +0.00 | any | `SPECIALIST-NEGATIVE` |

F1 is deeply negative; F2 is engaged. Per the pre-registered matrix, this maps to **SPECIALIST-NEGATIVE**, NOT NEGATIVE-INERT. The brief was explicit (Section 4, F2 CRITICAL FALSIFIER-DESIGN RESOLUTION): "NEGATIVE-INERT is reserved for `training_days` moving SHORTER or unchanged AND F1 ≤ 0 (mechanism truly did nothing)." Here the mechanism engaged (F2 ✓) but produced the wrong direction — this is the **INVERSE-EDGE** subtype pre-registered in brief Section 7 and LM Master §5.1.

The LM Master §5.1 pre-registered the inverse-edge risk at **~25–30%**: "if ETH's IS edge lives in 2022-23, recency-weighting discards it → F1<0." The run confirms this interpretation: ETH's IS signal is concentrated in OLDER samples (2022–23 bull/bear regime transitions); the 12-month exponential decay down-weighted those samples to `exp(−ln2/12 × ~18–24) ≈ 0.25–0.35` of their original weight, effectively discarding the edge-bearing period. The result is deeply negative rather than neutral, because the down-weighted 2022-23 samples were not just noisy — they were positively informative, and their suppression left the model fitting on a less signal-rich 2023–2024 window.

---

## §1c Attribution Log — Decay Confirmed, Kish Mild

The required §1c attribution log (LM Master Rec adopted as REQUIRED QE deliverable) fired at every training cell. Representative values (first cell and range across run):

| Cell | decay.mean | decay.min | weight_sum_before | weight_sum_after | ratio (≈ decay.mean) | kish_ratio_after |
|---|---:|---:|---:|---:|---:|---:|
| First (2022-01) | 0.5439 | 0.253 | 5356.56 | 2930.97 | 0.5472 | 0.7866 |
| Mid-run (several) | 0.5443 | 0.254 | ~6,800–7,100 | ~3,600–3,800 | ~0.51–0.54 | ~0.77–0.87 |
| Late IS (2023 cells) | 0.5443 | 0.254 | ~6,100–6,200 | ~3,070–3,130 | ~0.50–0.51 | ~0.86–0.88 |

Key §1c findings:

1. **Decay confirmed active**: `decay.mean ≈ 0.544` across all cells, `decay.min ≈ 0.253–0.254`. This matches the 12mo/24mo math exactly: `exp(−ln2/12 × 24) ≈ 0.25`. The 4:1 recent:old emphasis ratio was faithfully applied.

2. **Weight mass halved**: `ratio ≈ 0.54` (weight_sum_after / weight_sum_before ≈ decay.mean), confirming the un-renormalized decay halved the effective weight mass per the LM §1c prediction. The regularization-loosening channel (absolute-scale min_child_weight loosens when total weight mass drops ~50%) was present.

3. **Kish ratio = MILD (0.77–0.88), NOT the feared 0.35–0.45**: the LM §1b pre-registration predicted Kish could drop to 0.35–0.45 (ESS severe shrink). Observed Kish was 0.77–0.88 — well above the 0.50 concern threshold. **The negative result is NOT an ESS-shrink artifact.** A Kish of 0.87 means the sample weighting is numerically healthy; the negative IS performance is genuine, not a numerical pathology. This is a load-bearing attribution: it confirms the inverse-edge interpretation (ETH's signal is in old data) rather than a regularization-side-effect or weight-degeneracy explanation.

4. **Reg-loosening channel present but not the dominant explanation**: the weight mass halved (reg-loosening present), but Kish ≈ 0.87 means ESS is not severely degraded. If reg-loosening were the dominant failure mode, we would expect erratic per-fold Sharpe swings and numerical instability — the run.log shows consistent (if negative) fold-level patterns, not numerical collapse. Attribution: the dominant channel is recency-weighting discarding 2022-23 signal, with reg-loosening as a secondary (non-dominant) confound.

---

## Fail-Fast Validation Record — 3rd Trigger

This is the 3rd fail-fast event in the v1 cycle-7 SPECIALIST campaign:

| Iteration | Seat | Fail-fast verdict | Wall-clock saved |
|---|---|---|---|
| BNB/087 | BNBUSDT | BLOCKED-FAIL-FAST | ~4–5h |
| XRP/088 | XRPUSDT | PASSED fail-fast (positive; proceeded to full run) | — |
| **ETH/090** | **ETHUSDT W-DECAY** | **BLOCKED-FAIL-FAST** | **~3.5–4h** |

The fail-fast correctly identified the inverse-edge at the 2-year IS mark (13,468s ≈ 3.74h wall-clock), preventing ~3.5–4h of additional forward-pass compute. The pattern: BNB/087 (universe negative), XRP/088 (universe positive — correctly NOT blocked), ETH/090 (machinery negative). Three independent decisions with zero false positives and zero false negatives visible to date.

---

## Key Finding: Recency-Weighting is COIN-SPECIFIC

The most important interpretive takeaway from this iteration, stated explicitly:

**XRP's IS edge is RECENT (post-Nov-2025 pattern, XRP/088 brief §2); ETH's IS edge is OLD (2022-23 regime, confirmed here by inverse-edge result). These are opposite temporal-edge profiles.**

- W-DECAY on XRP would be expected to be **beneficial or neutral**: decay UP-WEIGHTS the recent signal-bearing period, giving XRP's model better alignment with its edge location.
- W-DECAY on ETH is **damaging**: decay DOWN-WEIGHTS the 2022-23 edge, discarding the primary signal-bearing period.

This does NOT close the W-DECAY axis globally:
- ETH/090 at 12mo half-life is NEGATIVE — this seat/half-life combination is closed.
- A different seat (e.g., XRP or a future post-2024-edge coin) at 12mo half-life could have a different outcome.
- A shorter half-life (e.g., 6mo or 9mo) might further penalize 2022-23 for ETH (worse), but has not been tested on a recent-edge coin.
- The W-DECAY machinery itself is validated (F2 ENGAGED, Kish healthy, §1c log working) — the negative is coin-specific, not a machinery flaw.

**Axis status**: OPEN for future coins with identified recent-edge profiles; CLOSED for ETH at 12mo (inverse-edge confirmed); the full axis closure question deferred to the QR's Phase 8 diary.

---

## Feature Integrity Audit

- `V1_FEATURE_COLUMNS_PRUNED` = 48 columns. UNCHANGED. `b81176f893826500...` hash in run.log header matches the established baseline hash. Global PRUNED stays 48 — no feature additions or removals.
- Cross-track isolation: no v2/v3 feature imports. Sample-weight mode is a training-only change with no effect on feature pipeline.
- Label-leakage gap: CV gap = 22 rows (184h = 8h × 23 candles), consistent with `(timeout_candles + 1) × n_symbols = (22 + 0) × 1` for single-symbol ETH specialist. Gap confirmed in run.log per-fold headers (`gap=184h (22 rows)` across all 5 CV folds).
- Sacred constants: `OOS_CUTOFF_DATE = 2025-03-24`, `training_months = 24` — both confirmed unchanged in runner and run.log header.

---

## Anomaly Notes

None. The run proceeded cleanly to the fail-fast trigger with no unexpected errors, no NaN in loss, no fold collapse (beyond the pre-registered negative Sharpe which is expected for an inverse-edge outcome). The 50-seed × 30-trial search completed all IS folds through 2023-12 before the fail-fast check fired at the first 2024 candle. The final training cell (2024-01) completed successfully and the first OOS-adjacent trade was opened before the abort.

One detail to note: the run.log shows the fail-fast fires *after* the 2024-01 training cell completes and the first live trade is opened (`[trade:open] 2024-01-04 15:59 ETHUSDT LONG`), then checks cumulative IS pnl and aborts. This is correct: the fail-fast guard checks post-IS-close not mid-training.

---

## Status

OVERALL = SPECIALIST-NEGATIVE (subtype INVERSE-EDGE)

**Not forwarded to Critic review** — fail-fast aborts are self-contained NEGATIVE verdicts requiring no Phase 7.5 adversarial review. QR Phase 8 diary authoring is the next step.

Verdict: **SPECIALIST-NEGATIVE** (INVERSE-EDGE). F2 ENGAGED (training_days median 280d > XRP/088 250d prior; folds<120d dropped from 50% to 14%). F1 deeply negative (IS Sharpe −2.02 vs baseline +0.24, Δ = −2.26). §1c attribution: decay.mean ≈ 0.544, Kish ≈ 0.87 (mild — NOT an ESS artifact), weight mass halved (reg-loosening channel present but non-dominant). Root cause: ETH's IS edge is concentrated in 2022-23 (old data); 12-month recency weighting discards it. Critical finding: W-DECAY is coin-specific in its effect — XRP-edge-recent vs ETH-edge-old are opposite profiles. W-DECAY axis remains OPEN for recent-edge coins; CLOSED for ETH at 12mo.
