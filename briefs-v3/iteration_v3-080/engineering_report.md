# Engineering Report — iter-v3/080

## Headers

- Iteration: iter-v3/080
- Branch: iteration-v3/080 (cycle-2 shared branch, iteration-v3/047)
- Commit chain (EDA → brief → SHAs backfill → setup → Phase 5.5 gate → implementation):
  - EDA: `0029155` — `analysis/iteration_v3-080/axis_selection_eda.py` + 6 output CSVs
  - Brief: `6df3d04` — `briefs-v3/iteration_v3-080/research_brief.md`
  - Brief SHAs backfill: `ea0339e` — backfilled setup + gate SHAs in brief Section 10.3
  - Setup: `dec440e` — `run_baseline_v3.py` ITERATION_LABEL "v3-080" + runner-side conviction-derate revert
  - Phase 5.5 gate: `3d8afd7` — PASS
  - Implementation: `8e7e62b` — `lgbm.py` flat-weight revert + `backtest_models.py` / `backtest.py` / `iteration_report.py` confidence threading + `_write_confidence_distribution`
  - HEAD at report time: `8e7e62b`
- Hardware: WSL2 / Linux 6.6.114.1-microsoft-standard-WSL2
- Wall-clock time: 0.68h (within 2.0h EXPLORATION cap; `--skip-features` per setup)
- Run mode: `--exploration --clean-oof --skip-features` (`EXPLORATION_ENSEMBLE_SIZE = 3`, outer-42 lineage subset `[191664963, 1662057957, 1405681631]`)
- Seeds: `[191664963, 1662057957, 1405681631]` (outer=42 lineage subset)
- Total Optuna trials: 315 (3 seeds × 3 symbols × 35 trials)

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
| **SUSPICIOUS 8.4 — OOS-DOMINANT sub-mode** | IS shift < 0 AND OOS shift ≥ +0.20 | IS shift 0.0000 (ZERO — IS < 0 clause fails) | NO |
| **NULL-RESULT 8.5 — bit-identical roster** | IS n_trades=159, OOS n_trades=102–103, roster bit-identical on keys+weight_factor, shifts ≈ 0, deliverable produced | IS 159, OOS 103; keys bit-identical (0 added, 0 removed); 0 weight_factor diffs; IS shift 0.0000; OOS shift +0.0830 (data-extent drift within admitted range); **deliverable NOT fully produced** (wiring defect — see Section below) | **YES — fires (partial)** |
| NEGATIVE 8.2 | IS < −0.10 OR OOS < −0.20 | IS 0.0000 (> −0.10); OOS +0.0830 (> −0.20) | Does not apply (NULL-RESULT already fires) |
| PROMISING 8.1 | IS ≥ +0.10 AND OOS ≥ +0.20 AND not SUSPICIOUS | IS 0.0000 (< +0.10) | Does not apply |
| INERT 8.3 | Both shifts in-band AND roster NOT bit-identical AND not SUSPICIOUS | Roster IS bit-identical on keys+weight_factor | Does not apply |

**CLASSIFICATION: NULL-RESULT — with DELIVERABLE-DEFECT flag.**

NULL-RESULT fires first in the disjunctive order. The roster is bit-identical on all required keys and weight_factor values. The IS shift is exactly 0.0000 and the OOS shift +0.0830 falls within the data-extent-admitted range (brief Section 4.1: "± a small data-extent drift"). The bit-identical-roster condition (the primary criterion) holds. However: the brief Section 8.5 states the deliverable must be produced ("the diagnostic deliverable (the `confidence` column on `trades.csv` + `confidence_distribution.csv`) is produced"), and the deliverable has a wiring defect (see below). This is documented as a DELIVERABLE-DEFECT flag on the NULL-RESULT — the classification is not changed (SUSPICIOUS/NEGATIVE/INERT do not fire), but the defect means the iteration's instrumental value is zero until fixed.

**NO-MERGE. The PASSIVE-DIAGNOSTIC does NOT advance to the cycle-2 CONFIRMATION as an edge ingredient.**

---

## Bit-Identity Verification — the Load-Bearing Check

Verified by field diff of `/077` vs `/080` IS and OOS `trades.csv`:

### IS bit-identity (/077 vs /080)

| Symbol | /077 IS n | /080 IS n | Keys added | Keys removed | weight_factor diffs |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 73 | 73 | 0 | 0 | **0** |
| LDOUSDT | 11 | 11 | 0 | 0 | **0** |
| TRXUSDT | 75 | 75 | 0 | 0 | **0** |
| **TOTAL** | **159** | **159** | **0** | **0** | **0** |

The IS `(symbol, open_time)` key roster and all `weight_factor` values are **bit-identical** between /077 and /080. The /079 conviction-derate revert is complete at the call site (`lgbm.py:754` = `weight = 100`): zero IS trades carry a de-rated weight. The IS monthly Sharpe is exactly +0.8236 = the /077 anchor, corroborating IS bit-identity.

### OOS bit-identity (/077 vs /080)

| Split | /077 OOS n | /080 OOS n | Keys added | Keys removed | weight_factor diffs |
|---|---:|---:|---:|---:|---:|
| OOS total | 103 | 103 | 0 | 0 | **0** |

The OOS `(symbol, open_time)` key roster and weight_factor values are also bit-identical. No trade was added or removed.

---

## OOS Δ +0.0830 Root-Cause — Data-Extent Artifact

/080 OOS monthly Sharpe +0.2908 vs /077 OOS +0.2078 (Δ +0.0830). Both are the /060-config; /080 ran on ~1-day-fresher klines than /077.

**The sole cause is exactly one trade with changed close_time and pnl_pct:**

| Field | /077 value | /080 value | Change |
|---|---|---|---|
| symbol | LDOUSDT | LDOUSDT | — |
| open_time | 1778716799999 | 1778716799999 | same |
| exit_reason | end_of_data | end_of_data | same |
| close_time | 1778831999999 | 1778889599999 | +57600000ms (+16h / +2 candles) |
| pnl_pct | +1.8051% | +6.3435% | +4.5384% |
| net_pnl_pct | +1.7051% | +6.2435% | +4.5384% |
| weighted_pnl | +1.3129 | +4.8075 | +3.4946 |

This is the last LDO OOS `end_of_data` position. /080 ran on 2 additional candles of OOS data (the close_time extended 16h from 2026-05-15 07:59:59 UTC to 23:59:59 UTC). The position's exit_price moved from 0.380800 to 0.363200 (LDO declined further), increasing the SHORT position's pnl by +4.54%. The net OOS wpnl increase of +3.49 drove the OOS monthly Sharpe lift.

This is a **data-extent artifact** — a monotonic calendar effect. It is NOT an axis effect: the PASSIVE-DIAGNOSTIC axis makes no strategic change; no trade is added or removed; the /079 conviction-derate is fully reverted. The OOS Δ +0.0830 is benign and consistent with the brief Section 4.1's admitted "± a small data-extent drift."

---

## Deliverable Verification — WIRING DEFECT FOUND

### (a) `confidence` column in `trades.csv`

The `confidence` column is present in the `trades.csv` header (16 columns total, `confidence` last). However, **all 159 IS trades and all 103 OOS trades have an empty `confidence` value** — not a float, an empty string.

**Root cause: `RiskV2Wrapper.get_signal` drops `confidence` when reconstructing the outgoing `Signal`.**

In `src/crypto_trade/strategies/ml/risk_v2.py` at lines 367–372:

```python
new_weight = max(1, int(round(sig.weight * scale * cap_scale)))
return Signal(
    direction=sig.direction,
    weight=new_weight,
    tp_pct=sig.tp_pct,
    sl_pct=sig.sl_pct,
)
```

The `Signal` reconstructed by `RiskV2Wrapper` does NOT pass `confidence=sig.confidence`. The `confidence` value is set when `LightGbmStrategy.get_signal` returns its `Signal(direction=..., weight=100, ..., confidence=confidence)` (the implementation is correct in `lgbm.py`). But every backtest call path goes through `RiskV2Wrapper.get_signal`, which wraps the inner `LightGbmStrategy`. When `RiskV2Wrapper` rebuilds the `Signal` at line 367 to apply vol-scaling, it constructs a new `Signal` without `confidence=sig.confidence`, silently losing the value. The downstream `make_order` and `make_result` functions in `backtest.py` correctly copy `signal.confidence → Order.confidence → TradeResult.confidence` — but they receive `None` from the wrapper.

The `_write_trades_csv` correctly writes `f"{t.confidence:.6f}"` if non-None else `""`. Since all `TradeResult.confidence` values are `None`, every confidence field is written as empty.

This defect was NOT caught by the Phase 5.5 gate (the gate checks architecture and brief completeness, not runtime behavior) and was NOT caught by the pre-flight tests (which test the threading from lgbm.py → Signal → backtest.py in isolation, not through the RiskV2Wrapper).

### (b) `confidence_distribution.csv`

The `confidence_distribution.csv` is degenerate: it contains only 21 rows covering `PORTFOLIO / ALL_IS` bins, each with `n_trades = 0`. The per-symbol / per-IS-month blocks are absent because `_write_confidence_distribution` filters to `[(t.symbol, t.open_time, t.confidence) for t in is_trades if t.confidence is not None]`, which produces an empty list. Only the PORTFOLIO/ALL_IS block is written (the code's fallback path for no data), and it shows zero trades in every confidence bin.

The `realized_optuna_conf_threshold` overlay is also degenerate: `sym_threshold` is populated by inspecting `model_pairs` strategy objects, but the code looks for `hasattr(inner, "_confidence_threshold")` after unwrapping `strat.inner`. The actual runner wraps strategies in `RiskV2Wrapper`, not a `.inner` attribute — the sym_threshold dictionary may be populated with a single portfolio-level value (0.642 observed in the CSV) rather than per-symbol values, but this is moot given the zero trade counts.

**The brief's secondary deliverable falsifier (Section 4.2) fires: "if `confidence_distribution.csv` is emitted but is degenerate... the diagnostic value is reduced."** More precisely, the PRIMARY deliverable also fails — the `confidence` column on `trades.csv` is the load-bearing instrument, and it is unpopulated. The iteration's diagnostic value is zero.

### Fix required before cycle-3 re-attempt

The fix is one line in `RiskV2Wrapper.get_signal` (lines 367–372):

```python
return Signal(
    direction=sig.direction,
    weight=new_weight,
    tp_pct=sig.tp_pct,
    sl_pct=sig.sl_pct,
    confidence=sig.confidence,   # <-- add this line
)
```

This fix must be applied and the backtest re-run before the confidence instrument is usable. The re-run will produce a bit-identical trade roster (same keys, same weight_factor, same Sharpe) with populated `confidence` values. The fix is the QR's decision to authorize (it is a Phase-6 wiring defect, not a research decision); the Engineer implements it.

---

## /079 Conviction-Derate Revert — Completeness Verification

`lgbm.py` line 754: `weight = 100` (flat). Confirmed by grep and by the IS bit-identity (zero IS weight_factor diffs vs /077, meaning no IS trade was de-rated). The `conviction_derate` helper remains defined as dead code (lines 114–137) — it is unreferenced from the call site and harmless. The runner no longer imports or asserts on it.

**The /079 conviction-derate revert is COMPLETE at the behavioral call site.** The RiskV2Wrapper wiring defect (Section above) is an independent bug that affects the `confidence` threading, not the weight-scalar revert.

---

## Seed Concentration Audit

Single-axis EXPLORATION (outer=42 lineage, 3 seeds). IS total wpnl = 51.73: BCH +77.61 (bit-identical to /077 except for rounding on the /061 vol_scale_floor), LDO −11.44, TRX −14.44. OOS: TRX dominant at 211% of total OOS wpnl (LDO is a large drag). PBO = 0.1278, frac_positive_paths = 0.644 — identical to the /060-config anchor. The 30% per-symbol cap is a CONFIRMATION gate; informational here.

---

## Label Leakage Audit

- `REQUIRED_GAP = 66 = (21 + 1) × 3 symbols` — confirmed unchanged.
- Embargo = 22 candles — unchanged.
- `V3_ATR_MULTIPLIERS_PER_SYMBOL = {}` confirmed: all symbols use `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)`.
- The passive `confidence` field is sourced from `directional_conf = max(float(proba[0]), float(proba[2]))` (or `max(proba)` for 2-class) at `lgbm.py:673/676` — computed from the same past-only `predict_proba` call the direction signal already uses. It is look-ahead-clean by construction.
- Walk-forward lookahead-bias note (`feedback_v3_walkforward_lookahead_bug.md`) applies equally to /080 (the embargo fix `e149e9d` is in this worktree; IS/OOS deltas vs /077 are valid; absolute magnitudes biased upward as with all cycle-2 iterations).

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

1. **Spot-check 10 random OOS trades — 0 math errors.** Verified `pnl_pct` formula (`direction == 1`: `(exit-entry)/entry × 100`; `direction == -1`: `(entry-exit)/entry × 100`). Exit reasons consistent (take_profit, stop_loss, timeout, end_of_data). No zero-trade OOS months (14 OOS months, all with positive trade counts). IS monthly_pnl: 33 rows, all non-zero.

2. **WIRING DEFECT: `confidence` column all-empty. `confidence_distribution.csv` degenerate.** `RiskV2Wrapper.get_signal` (lines 367–372) reconstructs `Signal` without `confidence=sig.confidence`. Confidence is set correctly in `lgbm.get_signal` and the backtest.py threading is correct, but the wrapper intercepts every call and drops the value. Fix is one keyword argument in `risk_v2.py:RiskV2Wrapper.get_signal`. This must be fixed and the backtest re-run before the confidence instrument is usable as a cycle-3 diagnostic.

3. **IS Sharpe = +0.8236 exactly.** Matches the re-anchored /060-config baseline. IS bit-identity confirmed mechanically (0 weight_factor diffs vs /077, 0 added/removed IS keys). The conviction-derate revert is complete.

4. **OOS Δ +0.0830 is a pure data-extent artifact.** One LDO `end_of_data` trade (open_time=1778716799999) resolved with 2 additional candles: close_time extended +16h, pnl_pct went from +1.8051% to +6.3435%, weighted_pnl from +1.3129 to +4.8075. This is the only differing OOS trade vs /077. The bit-identity on keys and weight_factor holds; the pnl change is from data freshness, not axis effect.

5. **PBO = 0.1278, frac_positive_paths = 0.644** — identical to /060-config anchor. No change expected from a bit-identical roster. Corroborates IS bit-identity and the null-effect of the passive-diagnostic axis.

6. **No NaN Sharpe, no zero-trade IS months, no NaN PnL.** IS monthly_pnl.csv: 33 rows, all with positive trade_count. OOS: 14 rows, all clean.

7. **Feature importance (last walk-forward month portfolio)** — 14 features, identical to /079:

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

Identical to /079 distribution — expected for a bit-identical run. No pathological concentration.

---

## ADF and IC Matrix Notes

ADF: 2198 rows emitted (BCH 63 months × 14 feats = 882; TRX 63 × 14 = 882; LDO 31 × 14 = 434; total 2198). Within the expected [1302, 2646] band. 82.0% cells stationary (p<0.05). No warnings in `run.log` (0 WARNING lines). IC matrix: 14 × 14 confirmed.

---

## Status

OVERALL = READY-FOR-CRITIC

**Classification: NULL-RESULT (PASSIVE-DIAGNOSTIC, bit-identical roster) with DELIVERABLE-DEFECT — NO-MERGE.**

**The DELIVERABLE-DEFECT must be resolved before the confidence instrument is usable.** The `RiskV2Wrapper.get_signal` wiring defect (missing `confidence=sig.confidence` in the reconstructed `Signal` at `risk_v2.py` lines 367–372) silently dropped every per-trade confidence value. The `confidence` column in `trades.csv` is present but all-empty (159 IS + 103 OOS rows). `confidence_distribution.csv` is degenerate (21 PORTFOLIO/ALL_IS rows, all n_trades=0). The fix is one keyword argument. Decision on whether to re-run /080 or carry the fix into cycle-3 setup is QR scope.

The bit-identity between /080 and /077 IS confirmed (159 IS keys, 0 weight_factor diffs; OOS 103 keys, 0 weight_factor diffs). IS Sharpe = +0.8236 exactly. OOS Δ +0.0830 is a pure data-extent artifact (one LDO `end_of_data` trade resolved with 2 additional candles). The /079 conviction-derate is fully reverted (flat `weight = 100` at `lgbm.py:754`).

---

Phase 6 complete. Engineering report committed. Phase 7.5 Critic review required before Phase 7. Orchestrator: invoke `quant-critic` with branch=`iteration-v3/080`, report_dir=`reports-v3/iteration_v3-080`, brief_dir=`briefs-v3/iteration_v3-080`.
