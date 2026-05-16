# Engineering Report — iter-v3/080

## Headers

- Iteration: iter-v3/080
- Branch: iteration-v3/080 (cycle-2 shared branch, iteration-v3/047)
- Commit chain (EDA → brief → SHAs backfill → setup → Phase 5.5 gate → implementation → confidence-wiring fix):
  - EDA: `0029155` — `analysis/iteration_v3-080/axis_selection_eda.py` + 6 output CSVs
  - Brief: `6df3d04` — `briefs-v3/iteration_v3-080/research_brief.md`
  - Brief SHAs backfill: `ea0339e` — backfilled setup + gate SHAs in brief Section 10.3
  - Setup: `dec440e` — `run_baseline_v3.py` ITERATION_LABEL "v3-080" + runner-side conviction-derate revert
  - Phase 5.5 gate: `3d8afd7` — PASS
  - Implementation: `8e7e62b` — `lgbm.py` flat-weight revert + `backtest_models.py` / `backtest.py` / `iteration_report.py` confidence threading + `_write_confidence_distribution`
  - **Confidence-wiring fix: `d71adf6`** — `RiskV2Wrapper.get_signal` + `RiskV3Wrapper.get_signal` both now forward `confidence=sig.confidence` when reconstructing the outgoing `Signal`; extended wrapper-chain regression test added
  - **Re-run** after `d71adf6`: reports in `reports-v3/iteration_v3-080/` overwrite the defective prior run
  - HEAD at report time: `d71adf6`
- Hardware: WSL2 / Linux 6.6.114.1-microsoft-standard-WSL2
- Wall-clock time: 0.68h (within 2.0h EXPLORATION cap; `--skip-features` per setup)
- Run mode: `--exploration --clean-oof --skip-features` (`EXPLORATION_ENSEMBLE_SIZE = 3`, outer-42 lineage subset `[191664963, 1662057957, 1405681631]`)
- Seeds: `[191664963, 1662057957, 1405681631]` (outer=42 lineage subset)
- Total Optuna trials: 315 (3 seeds × 3 symbols × 35 trials)

### First-Run Defect and Re-Run

The first /080 run (reports overwritten) had an empty-`confidence` deliverable defect. The `confidence` column was present in `trades.csv` (16 columns, `confidence` last) but all 159 IS + 103 OOS rows had an empty string value — not a float. `confidence_distribution.csv` was degenerate (21 PORTFOLIO/ALL_IS rows, all n_trades=0).

Root cause: two drop points in the wrapper chain. `RiskV2Wrapper.get_signal` (the call path every backtest trade takes) reconstructed its outgoing `Signal` from the inner `LightGbmStrategy` result without passing `confidence=sig.confidence`. `RiskV3Wrapper.get_signal` had the identical omission. `lgbm.get_signal` set `confidence` correctly; `backtest.py`'s `make_order` / `make_result` threaded it correctly; both wrapper reconstruction sites silently dropped it. The fix at `d71adf6` adds `confidence=sig.confidence` at both reconstruction call sites and extends the wrapper-chain regression test to assert the field survives the full `lgbm → RiskV2Wrapper → make_order → make_result` path end-to-end. The re-run produced a bit-identical trade roster (same keys, same weight_factor, same Sharpe) with all confidence values populated.

---

## Configuration Diff vs /060 EXPLORATION-MODE ANCHOR (re-anchored)

Anchor: IS +0.8236 / OOS +0.2078 (the current-code /060-config re-anchor established by /077; stale frozen /060 anchor NOT used).

| Parameter | /060-config anchor | /080 |
|---|---|---|
| `V3_MODELS` | BCH + LDO + TRX | **BCH + LDO + TRX** (unchanged; /078 ADA universe-revision axis CLOSED, LDO restored at /079) |
| Conviction-derate (primitive 13) | absent | **REVERTED** — `/079` `conviction_derate(confidence)` → `weight = 100` (flat) |
| Primary axis | — | PASSIVE-DIAGNOSTIC: `confidence` field threaded `Signal → Order → TradeResult`; `_write_confidence_distribution` emits `confidence_distribution.csv` |
| `ITERATION_LABEL` | `"v3-060"` | `"v3-080"` |
| All other params (features, labeling, risk gates, seeds, n_trials) | — | UNCHANGED |

Sacred constants confirmed: `OOS_CUTOFF_DATE = "2025-03-24"`, `TRAINING_MONTHS = 24`. `REQUIRED_GAP = 66 = (21+1) × 3`. The /059 CONFIRMATION baseline (IS +1.0894 / OOS +0.5791) is the canonical merge baseline and is NOT the EXPLORATION anchor; it is unchanged.

---

## Key Metrics Block

### Headline vs re-anchored current-code /060-config baseline (brief Section 4.1 prediction in parentheses)

| Metric | Anchor IS | /080 IS | IS Δ | Anchor OOS | /080 OOS | OOS Δ | /080 OOS/IS ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| monthly_sharpe | +0.8236 | **+0.8236** | **0.0000** | +0.2078 | **+0.2908** | **+0.0830** | **0.3531** |
| daily_sharpe | — | +1.7028 | — | — | +0.7647 | — | 0.4491 |
| max_drawdown | — | 32.04% | — | — | 35.89% | — | 1.1201 |
| profit_factor | — | 1.2773 | — | — | 1.1019 | — | 0.8627 |
| win_rate | — | 31.4% | — | — | 39.8% | — | 1.2658 |
| n_trades | ~159 (anchor) | **159** | **0** | ~103 (anchor) | **103** | **0** | 0.6478 |
| total_pnl | — | 51.7289 | — | — | 11.7129 | — | 0.2264 |
| monthly_calmar | — | 1.6144 | — | — | 0.3263 | — | 0.2021 |
| pbo | 0.1278 (anchor) | **0.1278** | 0 | — | — | — | — |
| psr | — | 1.0000 | — | — | — | — | — |
| dsr | 0.0 (anchor) | 0.0 | — | — | — | — | — |
| dsr_relative_b4 | — | 0.4963 | — | — | — | — | — |
| frac_positive_paths | 0.644 (anchor) | **0.644** | **0** | — | — | — | — |
| n_trials | 315 | 315 | 0 | — | — | — | — |
| n_effective_trials | 19 | 19 | 0 | — | — | — | — |

Note: DSR/PSR/DSR_relative_b4 are informational only at EXPLORATION mode (n_trials=315; EXPLORATION-mode DSR is a structural artifact per `feedback_v3_dsr_mode_artifact.md`).

### Per-symbol OOS section (`comparison.csv` per_symbol block)

| Symbol | weighted_pnl | n_trades | win_rate | concentration_pct |
|---|---:|---:|---:|---:|
| BCHUSDT | +1.9078 | 37 | 32.4% | 16.29% |
| LDOUSDT | −14.9133 | 12 | 25.0% | −127.32% |
| TRXUSDT | +24.7184 | 54 | 48.1% | 211.04% |

The 30% per-symbol cap is a CONFIRMATION gate; informational here.

---

## Classification per Brief Section 8 LOCKED

Evaluation order per brief: SUSPICIOUS (8.4) → NULL-RESULT (8.5) → NEGATIVE (8.2) → PROMISING (8.1) → INERT (8.3). First match is canonical. Anchor: IS +0.8236 / OOS +0.2078 (re-anchored).

| Gate | Threshold | /080 result | Fires? |
|---|---|---|---|
| **SUSPICIOUS 8.4 — OOS/IS ratio > 3.0** | > 3.0 | **0.3531** | NO |
| **SUSPICIOUS 8.4 — OOS-DOMINANT sub-mode** | IS shift < 0 AND OOS shift ≥ +0.20 | IS shift **0.0000** (ZERO — IS < 0 clause fails) | NO |
| **NULL-RESULT 8.5 — bit-identical roster** | IS n_trades=159, OOS n_trades=102–103, roster bit-identical on keys+weight_factor, shifts ≈ 0, deliverable produced | IS 159, OOS 103; keys bit-identical (0 added, 0 removed vs /077); 0 weight_factor diffs vs /077; IS shift 0.0000; OOS shift +0.0830 (data-extent drift within admitted range); deliverable NOW SOUND (confidence column fully populated; `confidence_distribution.csv` non-degenerate) | **YES — fires** |
| NEGATIVE 8.2 | IS < −0.10 OR OOS < −0.20 | IS 0.0000 (> −0.10); OOS +0.0830 (> −0.20) | Does not apply (NULL-RESULT already fires) |
| PROMISING 8.1 | IS ≥ +0.10 AND OOS ≥ +0.20 AND not SUSPICIOUS | IS 0.0000 (< +0.10) | Does not apply |
| INERT 8.3 | Both shifts in-band AND roster NOT bit-identical AND not SUSPICIOUS | Roster IS bit-identical on keys+weight_factor | Does not apply |

**CLASSIFICATION: NULL-RESULT.**

The roster is bit-identical on all required keys and weight_factor values. IS shift is exactly 0.0000 and OOS shift +0.0830 falls within the data-extent-admitted range (brief Section 4.1: "± a small data-extent drift"). The bit-identical-roster condition holds. The deliverable is now sound (confidence column fully populated; `confidence_distribution.csv` non-degenerate with 2016 rows, 315 non-zero-trade bins, genuine per-symbol histograms with per-symbol Optuna threshold overlay).

**NO-MERGE. The PASSIVE-DIAGNOSTIC does NOT advance to the cycle-2 CONFIRMATION as an edge ingredient.**

---

## Bit-Identity Verification — the Load-Bearing Check

The re-run is bit-identical to the pre-fix /080 run: the confidence-wiring fix (`d71adf6`) touches no decision path — it forwards a metadata field that no model, gate, or barrier reads. The trade roster (keys, weight_factor, pnl, Sharpe) is identical between the defective and corrected runs.

### IS bit-identity (/080 re-run vs /077 anchor)

| Symbol | /077 IS n | /080 IS n | Keys added | Keys removed | weight_factor diffs |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 73 | 73 | 0 | 0 | **0** |
| LDOUSDT | 11 | 11 | 0 | 0 | **0** |
| TRXUSDT | 75 | 75 | 0 | 0 | **0** |
| **TOTAL** | **159** | **159** | **0** | **0** | **0** |

The IS `(symbol, open_time)` key roster and all `weight_factor` values are **bit-identical** between /077 and /080 re-run. IS monthly Sharpe exactly +0.8236 = the re-anchored /060-config baseline, corroborating IS bit-identity mechanically.

### OOS bit-identity (/080 re-run vs /077 anchor)

| Split | /077 OOS n | /080 OOS n | Keys added | Keys removed | weight_factor diffs |
|---|---:|---:|---:|---:|---:|
| OOS total | 103 | 103 | 0 | 0 | **0** |

The OOS `(symbol, open_time)` key roster and weight_factor values are also bit-identical between /077 and /080. No trade was added or removed. (The one LDO OOS trade that differs has identical key and weight_factor but different pnl_pct from data-extent drift — see next section.)

### /079 conviction-derate revert confirmed

The IS weight_factor comparison between /079 and /080 shows exactly 12 differences — the 12 IS trades /079's conviction-derate re-weighted, now restored to flat weight (6 BCH trades, 6 TRX trades). OOS shows exactly 1 difference — the single TRX OOS de-rated trade, restored. Zero LDO diffs in either split. The revert is complete at `lgbm.py:754` = `weight = 100`. The `conviction_derate` helper remains defined as dead code.

---

## OOS Δ +0.0830 Root-Cause — Data-Extent Artifact

/080 OOS monthly Sharpe +0.2908 vs /077 OOS +0.2078 (Δ +0.0830). Both are the /060-config; /080 ran on approximately 1-day-fresher klines than /077.

**The sole cause is exactly one trade with changed close_time and pnl_pct:**

| Field | /077 value | /080 value | Change |
|---|---|---|---|
| symbol | LDOUSDT | LDOUSDT | — |
| open_time | 1778716799999 | 1778716799999 | same |
| weight_factor | 0.770 | 0.770 | same (bit-identical) |
| exit_reason | end_of_data | end_of_data | same |
| close_time | 1778831999999 | 1778889599999 | +57600000ms (+16h / +2 candles) |
| pnl_pct | +1.8051% | +6.3435% | +4.5384% |
| net_pnl_pct | +1.7051% | +6.2435% | +4.5384% |
| weighted_pnl | +1.3129 | +4.8075 | +3.4946 |

This is the last LDO OOS `end_of_data` position. /080 ran on 2 additional candles of OOS data (the close_time extended 16h from 2026-05-15 07:59:59 UTC to 23:59:59 UTC). The net OOS wpnl increase of +3.49 drove the OOS monthly Sharpe lift.

This is a **data-extent artifact** — a monotonic calendar effect. It is NOT an axis effect: the PASSIVE-DIAGNOSTIC axis makes no strategic change; no trade is added or removed; the /079 conviction-derate is fully reverted. The OOS Δ +0.0830 is benign and consistent with the brief Section 4.1's admitted "± a small data-extent drift." The SUSPICIOUS 8.4 OOS-DOMINANT sub-mode requires IS shift < 0 — observed IS shift is exactly 0.0000 — so it does not fire regardless of the OOS magnitude.

---

## Deliverable Verification — NOW SOUND

The confidence-wiring fix (`d71adf6`) resolves both drop points in the wrapper chain. This section confirms the re-run deliverable is fully sound.

### (a) `confidence` column in `trades.csv` — FULLY POPULATED

All 262 IS+OOS trades carry a real per-trade M1 confidence value.

| Split | Total trades | Populated | Empty | Range | Mean |
|---|---:|---:|---:|---|---:|
| IS | 159 | **159** | 0 | [0.5429, 0.9943] | 0.7767 |
| OOS | 103 | **103** | 0 | [0.6257, 0.9981] | 0.8099 |

All values are in [0.50, 1.00], consistent with `max(P(long), P(short))` from a 3-class classifier where the inactive class has P≈0. No degenerate values (no 0.5 floor pile-up, no 1.0 pile-up). The 10-trade OOS spot-check (see Anomaly Notes) verified all confidence values are real floats and the pnl math is correct.

This deliverable now discharges the iter-v3/079 Critic Recommendation #1 methodology debt: the per-trade M1 confidence is persisted to a committed report artifact. A future cycle-3 conviction-derate re-attempt has the data to place C_REF empirically.

### (b) `confidence_distribution.csv` — NON-DEGENERATE

2016 rows (header + 2016 data rows). Genuine per-symbol / per-IS-month histograms with the realized Optuna `confidence_threshold` per cell overlaid.

| Symbol | IS months covered | Non-zero trade bins | Realized threshold (last-month) |
|---|---:|---:|---:|
| BCHUSDT | 29 | 188 | 0.6893 |
| LDOUSDT | 11 | 18 | 0.6507 |
| TRXUSDT | 30 | 109 | 0.5859 |
| PORTFOLIO | — | 18 | 0.6420 |

Total n_trades across all rows: 636 (IS trades counted across all month-symbol-bin combinations; the per-IS-month histogram aggregates each IS trade once per its (symbol, month, bin) cell, so pooled ALL_IS blocks double-count). The PORTFOLIO/ALL_IS distribution is non-degenerate: trades spread across bins [0.525, 0.975+).

The `realized_optuna_conf_threshold` overlay uses the last walk-forward month's per-symbol threshold (the lazy-monthly-training pattern the brief Section 7 anticipated). This is a single-point map per symbol, labeled implicitly as last_month values (the engineering constraint the brief pre-registered at Section 4.2 secondary falsifier). The per-IS-month `n_trades` histogram rows are fully populated from the now-complete per-trade `confidence` column.

### (c) What the distribution reveals — substantive finding

The distribution confirms the /079 NULL-RESULT root cause empirically. For each symbol, the realized Optuna threshold sits at or above ~0.59–0.69, and the surviving IS trades cluster overwhelmingly at or above the threshold:

| Symbol | Threshold | Trades strictly below threshold | Trades at/above threshold | Crossing-bin trades |
|---|---:|---:|---:|---:|
| BCHUSDT | 0.6893 | 15 | 55 | 3 |
| LDOUSDT | 0.6507 | 0 | 11 | 0 |
| TRXUSDT | 0.5859 | 3 | 70 | 2 |

LDO had **zero** IS trades below the 0.6507 threshold — every LDO IS signal had confidence ≥ 0.65. TRX had only 3 out of 75 trades strictly below its 0.5859 threshold. BCH had 15 out of 73 below 0.6893, but the majority of those sit in the [0.625, 0.6893) crossing range that would only partially overlap the /079 de-rate window [C_FLOOR=0.50, C_REF=0.65).

This empirically confirms the /079 mechanism: the a-priori `C_REF = 0.65` was placed at the Optuna threshold pile-up (BCH 0.6893, LDO 0.6507) rather than below it, leaving the de-rate window [0.50, 0.65) nearly empty of surviving signals. A cycle-3 conviction-derate re-attempt that places C_REF using this distribution — specifically, at a value where each symbol has materially more than 15% of its IS trades below the reference — is now empirically grounded.

---

## /079 Conviction-Derate Revert — Completeness Verification

`lgbm.py` line 754: `weight = 100` (flat). Confirmed by grep and by IS bit-identity (zero IS weight_factor diffs vs /077, per the /079→/080 diff showing exactly the 12 de-rated trades restored). The `conviction_derate` helper remains defined as dead code (lines 114–137) — unreferenced from the call site, harmless. The runner no longer imports or asserts on it.

**The /079 conviction-derate revert is COMPLETE at the behavioral call site.**

---

## Seed Concentration Audit

Single-axis EXPLORATION (outer=42 lineage, 3 seeds). IS total wpnl = 51.73: BCH +77.61, LDO −11.44, TRX −14.44. OOS: TRX dominant at 211% of total OOS wpnl (LDO is a large drag). PBO = 0.1278, frac_positive_paths = 0.644 — identical to the /060-config anchor, corroborating bit-identity. The 30% per-symbol cap is a CONFIRMATION gate; informational here.

---

## Label Leakage Audit

- `REQUIRED_GAP = 66 = (21 + 1) × 3 symbols` — confirmed unchanged.
- Embargo = 22 candles — unchanged.
- `V3_ATR_MULTIPLIERS_PER_SYMBOL = {}` confirmed: all symbols use `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)`.
- The passive `confidence` field is sourced from `directional_conf = max(float(proba[0]), float(proba[2]))` at `lgbm.py:673/676` — computed from the same past-only `predict_proba` call the direction signal already uses. It is look-ahead-clean by construction. The wrapper-chain fix at `d71adf6` only threads this value forward; it introduces no new data dependency.
- Walk-forward lookahead-bias note (`feedback_v3_walkforward_lookahead_bug.md`) applies equally to /080 (the embargo fix `e149e9d` is in this worktree). IS/OOS deltas vs /077 are valid; absolute magnitudes biased upward as with all cycle-2 iterations.

---

## Gate Efficacy Table

All risk gates unchanged from /060. No gate was modified.

| Primitive | State | IS fire rate | OOS note |
|---|---|---|---|
| 1 — Feature OOD z > 2.0 | ON | same as /060 anchor | same as /060 |
| 2 — Hurst regime | ON | same as /060 anchor | same as /060 |
| 3 — ADX gate | ON | same as /060 anchor | same as /060 |
| 4 — Low-vol filter | ON | same as /060 anchor | same as /060 |
| 5 — Vol-adjusted sizing | ON | same as /060 anchor | same as /060 |
| 6 — Per-symbol PnL cap | OFF | 0 | — |
| 7 — Drawdown brake (primitive 11) | OFF (CLOSED /054) | 0 | — |
| 9 — Regime kill switch | OFF (CLOSED) | 0 | — |
| 10 — Direction kill switch | OFF (reverted /051) | 0 | — |
| 12 — BTC-trend SIZE de-rate | OFF (reverted /076) | 0 | — |
| **13 — Conviction-derate** | **REVERTED** to flat weight=100 | 0 | 0 |

TRX `vol_scale_floor=0.5` (from /061) active and unchanged.

---

## Anomaly Notes

1. **Spot-check 10 random OOS trades — 0 math errors.** Verified `pnl_pct` formula (`direction == 1`: `(exit-entry)/entry × 100`; `direction == -1`: `(entry-exit)/entry × 100`). All 10 sampled OOS trades pass. Confidence values in the spot-check ranged from 0.693 (BCH) to 0.901 (TRX) — all real floats, none empty. Exit reasons (take_profit, stop_loss, timeout, end_of_data) are self-consistent. No zero-trade OOS months (14 OOS months, all with positive trade counts). IS monthly_pnl: 33 rows, all non-zero.

2. **IS Sharpe = +0.8236 exactly.** Matches the re-anchored /060-config baseline. IS bit-identity confirmed mechanically (0 weight_factor diffs vs /077, 0 added/removed IS keys). The conviction-derate revert is complete.

3. **OOS Δ +0.0830 is a pure data-extent artifact.** One LDO `end_of_data` trade (open_time=1778716799999) resolved with 2 additional candles: close_time extended +16h, pnl_pct went from +1.8051% to +6.3435%, weighted_pnl from +1.3129 to +4.8075. This is the only differing OOS field vs /077; keys and weight_factor are bit-identical. The SUSPICIOUS OOS-DOMINANT sub-mode requires IS shift < 0 — IS shift is exactly 0.0000 — so it cannot fire.

4. **PBO = 0.1278, frac_positive_paths = 0.644** — identical to /060-config anchor. No change expected from a bit-identical roster. Clean corroboration.

5. **No NaN Sharpe, no zero-trade IS months, no NaN PnL.** IS monthly_pnl.csv: 33 rows, all with positive trade_count. OOS: 14 rows, all clean.

6. **Feature importance (last walk-forward month portfolio)** — 14 features, identical to /079. Bit-identical run produces identical models and identical importance rankings. `regime_momentum_signed_5d` rank 14/14 (unchanged). No pathological concentration.

| Rank | Feature | Portfolio importance |
|---:|---|---:|
| 1 | ret_skew_200 | 816.3 |
| 2 | vwap_dev_20 | 759.7 |
| 3 | range_realized_vol_50 | 706.3 |
| 4 | ema_spread_atr_20 | 698.7 |
| 5 | max_dd_window_50 | 646.3 |
| 6 | ret_autocorr_lag1_50 | 607.0 |
| 7 | ret_kurt_50 | 598.0 |
| 8 | hurst_diff_100_50 | 593.3 |
| 9 | ret_kurt_200 | 582.0 |
| 10 | btc_ret_14d | 582.0 |
| 11 | hurst_100 | 569.3 |
| 12 | ret_skew_50 | 520.3 |
| 13 | sym_vs_btc_ret_7d | 511.7 |
| 14 | regime_momentum_signed_5d | 506.7 |

---

## ADF and IC Matrix Notes

ADF: 2198 rows emitted (BCH 63 months × 14 feats = 882; TRX 63 × 14 = 882; LDO 31 × 14 = 434; total 2198). Within the expected [1302, 2646] band. 82.0% cells stationary (p<0.05). No warnings in `run.log` (0 WARNING lines). IC matrix: 14 × 14 confirmed.

---

## Status

OVERALL = READY-FOR-CRITIC

**Classification: NULL-RESULT (PASSIVE-DIAGNOSTIC, bit-identical roster) — NO-MERGE.**

NULL-RESULT fires first in the disjunctive evaluation order (SUSPICIOUS (8.4) → NULL-RESULT (8.5) → NEGATIVE (8.2) → PROMISING (8.1) → INERT (8.3)). SUSPICIOUS does not fire: OOS/IS ratio = 0.3531 (< 3.0 gate); OOS-DOMINANT sub-mode requires IS shift < 0, observed IS shift is exactly 0.0000. NULL-RESULT fires on the bit-identical-roster condition: IS 159 trades (0 added, 0 removed vs /077 anchor), OOS 103 trades (0 added, 0 removed vs /077 anchor), 0 weight_factor diffs on any IS trade, IS shift = 0.0000, OOS shift = +0.0830 within the data-extent-admitted range (brief Section 4.1). The deliverable is produced and sound.

**The deliverable is now fully sound.** The `confidence` column in `trades.csv` is populated on all 262 IS+OOS trades (IS range [0.543, 0.994], OOS range [0.626, 0.998]). `confidence_distribution.csv` is non-degenerate: 2016 rows, 315 non-zero-trade bins, genuine per-symbol/per-IS-month histograms, per-symbol Optuna threshold overlay. This discharges the iter-v3/079 Critic Recommendation #1 methodology debt.

The distribution reveals the /079 NULL-RESULT root cause empirically: realized Optuna thresholds sit at 0.5859 (TRX), 0.6507 (LDO), and 0.6893 (BCH). The surviving IS trades cluster predominantly at or above these thresholds — only 15 BCH, 0 LDO, and 3 TRX IS trades sit strictly below their respective symbol thresholds. The /079 a-priori `C_REF = 0.65` landed at the LDO threshold pile-up and well below the BCH pile-up, leaving the intended de-rate window [0.50, 0.65) nearly empty of surviving signals. A cycle-3 conviction-derate re-attempt has the empirical data to place C_REF in the populated region of the distribution — below the per-symbol Optuna threshold pile-up — where it can engage a material fraction of IS trades (the ≥15% behavioral-effect floor required by Section 8.5).

The bit-identity between /080 and the /077 anchor is confirmed on all six symbol-split pairs (IS BCH/LDO/TRX and OOS BCH/LDO/TRX): zero keys added, zero keys removed, zero weight_factor diffs. IS Sharpe = +0.8236 exactly. The /079 conviction-derate is fully reverted (flat `weight = 100` at `lgbm.py:754`).

---

Phase 6 complete. Engineering report committed. Phase 7.5 Critic review required before Phase 7. Orchestrator: invoke `quant-critic` with branch=`iteration-v3/080`, report_dir=`reports-v3/iteration_v3-080`, brief_dir=`briefs-v3/iteration_v3-080`.
