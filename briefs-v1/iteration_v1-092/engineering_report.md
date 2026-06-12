# Engineering Report — iter-v1/092

## 1. Headers

- **Iteration**: iter-v1/092 (XRP-IMPROVED — BTC-trend-directional kill gate)
- **Track**: v1 (refactored), SPECIALIST
- **Branch**: `iteration-v1/092`
- **Code commit SHA (pre-backtest)**: `89852828` (Phase 6.0 v2 Critic pre-flight PASS; fix commit `77947a3d`)
- **Current HEAD**: `89852828`
- **Hardware**: WSL2 / x86-64 CPU / local machine
- **Wall-clock time (corrected backtest)**: ~25 min (single-seed EXPLORATION; 50 inner seeds x 30 trials x 54 walk-forward months / XRPUSDT only)
- **Cadence position**: Cycle-6/7 SPECIALIST #N — risk-primitive axis; EXPLORATION; NO baseline update

---

## 2. Dual-Run History (VOID + CORRECTED)

### Run 1: VOID (dispatch-wiring defect)

**Defect identified:** `run_baseline_v1.py` line 8385 dispatched ALL runs with `symbols={"XRPUSDT"}` to
the /088 branch via an `elif symbols == V1_ITER088_UNIVERSE` guard that was missing an `iteration_label`
check. Since `V1_ITER092_UNIVERSE == V1_ITER088_UNIVERSE == ("XRPUSDT",)`, the /092 branch (line 8990)
was dead code. The strategy built had `enable_btc_regime_kill=False`; the gate never armed; IS trades were
bit-identical to /088 (219 == 219 trades, IS Sharpe 0.3783 == 0.3783).

**Smoking gun missed:** `run.log` line 49 printed `[iter-v1/088]` banner (NOT `[iter-v1/092]`). This was
dismissed as cosmetic during liveness checks. A pre-registered liveness criterion in
`rerun_projection.md` explicitly named this as the indicator; the orchestrator did not verify it before
declaring the run valid.

**Process lesson:** the banner line is the FIRST liveness check. Void runs that pass metric plausibility
(reasonable trade count, non-zero Sharpe) but fail the banner check are non-trivial to detect without a
formal pre-registered checklist. Future dispatch bugs of this class are caught by: (a) the `iteration_label`
guard added by `77947a3d`, and (b) the new FAIL-LOUD assertion in `lgbm.py` (~line 644) that raises if
`enable_btc_regime_kill=True` but the gate index failed to load.

A 3-agent forensic (`analysis/iteration_v1-092/gate_fire_forensic.py`) diagnosed the defect. The VOID
run log is preserved at `reports-v1/iteration_v1-092/run_VOID_dispatch_bug.log`.

### Fix (commit `77947a3d`)

- Added `iteration_label == "v1-088" and` guard to line 8385 (the /088 elif).
- Added `iteration_label == "v1-087" and` guard to line 8191 (the /087 elif — sibling collision prevention).
- Added FAIL-LOUD assertion in `lgbm.py`: `enable_btc_regime_kill=True` with a failed BTC-candle index
  load now raises `RuntimeError` instead of silently no-op'ing.
- 30/30 tests PASS after fix.
- Critic Phase 6.0 v2 pre-flight PASS (commit `89852828`).

### Run 2: CORRECTED

Gate arm verified from `run.log` line 49:
```
[iter-v1/092] XRP SPECIALIST + BTC-regime kill gate: ... R6=ON BTC-regime kill thr=0.067 lookback=42b.
```
And line 52:
```
[lgbm] BTC-regime kill gate: loaded 7061 BTC candles from data/features/BTCUSDT_8h_features.parquet (thr=0.067, lookback=42b)
```

IS trade count: 179 (NOT 219) — gate was live and suppressing entries. OOS: 75 (NOT 84).

---

## 3. Configuration Diff vs /088 Anchor

| Parameter | /088 Anchor | iter-v1/092 | Status |
|---|---|---|---|
| Iteration label | v1-088 | v1-092 | changed |
| enable_btc_regime_kill | False | True | changed |
| btc_kill_threshold | N/A | 0.067 (IS abs-median) | new |
| btc_kill_lookback_bars | N/A | 42 bars (8h x 42 = 14d) | new |
| Feature columns | V1_FEATURE_COLUMNS_PRUNED (48 cols) | V1_FEATURE_COLUMNS_PRUNED (48 cols) | UNCHANGED |
| Seeds | single outer seed=42 | single outer seed=42 | UNCHANGED |
| Inner seeds (specialist) | 50 seeds x 30 trials | 50 seeds x 30 trials | UNCHANGED |
| ENSEMBLE_SIZE | 1 | 1 | UNCHANGED |
| max_depth | 5 (FIXED) | 5 (FIXED) | UNCHANGED |
| num_leaves | 31 (FIXED) | 31 (FIXED) | UNCHANGED |
| atr_tp / atr_sl | 2.9 / 1.45 | 2.9 / 1.45 | UNCHANGED |
| training_months | 24 | 24 | UNCHANGED (SACRED) |
| OOS_CUTOFF_DATE | 2025-03-24 | 2025-03-24 | UNCHANGED (SACRED) |
| PRUNED feature set | 48 cols | 48 cols | UNCHANGED |
| specialist_mode | True | True | UNCHANGED |
| R1 | OFF (CATALOG-CLOSED) | OFF | UNCHANGED |
| R2 | OFF (Model A baseline) | OFF | UNCHANGED |
| R3 | ON-SHARED cutoff=0.70 | ON-SHARED cutoff=0.70 | UNCHANGED |
| R5 | ON vt_target_vol=0.3 | ON vt_target_vol=0.3 | UNCHANGED |

**One-variable discipline: the ONLY change vs /088 is `enable_btc_regime_kill=True` with `thr=0.067, lookback=42b`.**

---

## 4. Key Metrics Block

### Ungated (/088 clone, void run) vs Gated (/092 corrected)

| Metric | Ungated IS (/088) | Gated IS (/092) | Ungated OOS (/088) | Gated OOS (/092) |
|---|---|---|---|---|
| sharpe | 0.3783 | **0.3007** | 0.5158 | **0.5952** |
| sortino | — | 0.2299 | — | 0.6802 |
| max_drawdown | 26.29% | **41.82%** | 18.90% | **15.78%** |
| win_rate | 42.5% | 44.7% | 42.9% | 45.3% |
| profit_factor | 1.1293 | 1.1222 | 1.1468 | 1.1845 |
| total_trades | 219 | **179** | 84 | **75** |
| calmar_ratio | — | 0.5720 | — | 0.7215 |
| total_net_pnl | 28.13 | 23.92 | 10.05 | 11.39 |
| OOS/IS ratio (sharpe) | — | — | — | 1.9792 |

### /092 vs BASELINE_V1 context

The current live baseline is BUNDLE-002 (`v0.v1-082`): IS +0.72 / OOS +1.00.
/092 is a SPECIALIST seat candidate for BUNDLE-003, not a baseline replacement.
The relevant anchor is /088 (the held PROMISING diversifier): IS +0.3783 / OOS +0.5158.

---

## 5. Falsifier Evaluation (F1–F4)

| Falsifier | Pre-registered criterion | Actual | Verdict |
|---|---|---|---|
| F1: IS Sharpe lift | IS Sharpe ≥ 0.578 (Δ≥+0.20 vs /088 0.3783) | **0.3007** (Δ = −0.078) | **FAILS HARD** |
| F2: Mechanism engagement (20–45% IS suppression) | 20–45% of IS entries suppressed | **18.3%** (40/219 net removed) | **BELOW BAND** |
| F3: OOS trades ≥ 50 | ≥ 50 OOS trades | 75 | PASS (moot given F1) |
| F4: Regime breadth | Pre-Nov OOS ≥ −5% AND ≥ 3/8 months pos | not evaluated (F1 hard fail) | MOOT |

**F1 FAILS HARD. IS Sharpe 0.3007 is worse than both the ungated /088 anchor (0.3783) AND the pre-registered F1 floor (0.578). The BTC-regime-kill gate degrades IS even when properly armed.**

**F2 BELOW BAND (18.3% not 20–45%):** the gate suppressed 65 gross entries (some from BTC_UP, some from reshuffled positions liberated by BTC_UP suppressions) but 25 new replacement entries were generated by the sequential position model, for a net of 40 removed (18.3%). The offline projection assumed 57 entries removed, 0 added — that assumption was wrong (see Section 7 and `analysis/iteration_v1-092/projection_divergence.py`).

---

## 6. Lock Verification (Sacred Constants)

| Lock item | Expected | Actual | Status |
|---|---|---|---|
| PRUNED feature columns | 48 | 48 | PASS |
| Inner seed count | 50 | 50 (seeds 42..91) | PASS |
| n_trials per cell | 30 | 30 | PASS |
| max_depth | 5 FIXED | 5 FIXED | PASS |
| num_leaves | 31 FIXED | 31 FIXED | PASS |
| atr_tp / atr_sl | 2.9 / 1.45 | 2.9 / 1.45 | PASS |
| training_months | 24 | 24 | PASS (SACRED) |
| OOS_CUTOFF_DATE | 2025-03-24 | 2025-03-24 | PASS (SACRED) |
| single outer seed | seed=42 | seed=42 | PASS |
| NO multi-seed CONFIRMATION | N/A | EXPLORATION only | PASS |

---

## 7. Projection-Falsification: Why Offline Subtraction Diverged

**Pre-registered projection (committed before corrected run):** IS 219→162 (−57, 26%), IS Sharpe
~+0.81 gain. OOS 84→72 (−12).

**Actual corrected result:** IS 219→179 (−40 net, 18.3%), IS Sharpe +0.3783→0.3007 (−0.078).

**Divergence decomposition:**

The projection's fatal flaw was asserting "0 overlapping trades" proves subtraction is exact. That claim
is true for STATIC overlaps between existing trades in the ungated roster. But the XRP position model is
SEQUENTIAL (one position at a time). Suppressing a BTC_UP entry at time T FREES the position slot —
allowing the strategy to enter a new position that was previously blocked because the slot was occupied.
The gate does not merely subtract; it reshuffles the downstream roster.

| Mechanism | Projection assumption | Actual |
|---|---|---|
| Gross removed (gate-suppressed) | 57 (all BTC_UP) | 65 (BTC_UP + downstream-freed reshuffled) |
| New replacements generated | 0 | 25 (sequential position slot freed) |
| Net trades removed | 57 | 40 |
| Removed trades WR | 0.3509 (EDA from /088 IS) | 0.3077 |
| Removed trades total wpnl | −5.21 (helpful to remove) | −17.10 (worse than projected — includes reshuffled losers) |
| Replacement trades WR | N/A | 0.2800 (below the removed WR) |
| Replacement trades total wpnl | N/A | −24.33 (losers dominate) |
| Net IS wpnl change | +5.21 (projected gain) | −7.23 (actual loss) |

**Conclusion:** the reshuffling created 25 replacement positions with WR 0.280 (below the 0.447 gated mean),
generating −24.33 wpnl that more than offset the benefit of removing the 65 suppressed trades (−17.10 wpnl).
IS went from 28.13 → 23.92, not to ~33.34 as projected.

**OOS:** the gate did modestly help OOS (the replaced entries had higher WR 0.500 vs removed WR 0.391,
net +1.28 wpnl, contributing to OOS Sharpe rising 0.5158→0.5952). But IS destruction overwhelms.

**Generalizable rule:** NEVER trust offline post-hoc trade-subtraction projections for ENTRY gates in
a path-dependent sequential backtest. The backtest is the only valid arbiter. The pre-registration
of the projection correctly identified this as the falsifier risk ("OOS Sharpe projection is an
OFFLINE APPROXIMATION") but did NOT extend that caveat to the IS projection, which was stated as
"analytically exact." That statement was wrong and is now falsified.

Full computation: `analysis/iteration_v1-092/projection_divergence.py` +
`analysis/iteration_v1-092/projection_divergence.md`.

---

## 8. Gate Efficacy Table

| Gate | IS fire rate | OOS fire rate | Note |
|---|---|---|---|
| R3 OOD | ON, SHARED | — | Fires as baseline |
| R5 vol-targeting | ON vt=0.3 | — | Fires as baseline |
| R6 BTC-regime kill (new) | VERIFIED ARMED | VERIFIED ARMED | 65 IS entries suppressed gross, 40 net; 23 OOS removed, 9 net |
| r5_fire_rate_is | 0.000 | 0.000 | As per comparison.csv |
| r5_binary_kill_fire_rate_is | 0.000 | 0.000 | As per comparison.csv |

---

## 9. Basin Diagnostics

From `basin_diagnostics/basin_diagnostics.json`:
- V1 cross_seed_sharpe_std = 0.000 — PASS (threshold 0.3; single outer seed, 50 inner seeds collapsed to
  mean; single combined prediction per candle, no per-outer-seed Sharpe variance to report)
- V2 per_cell_spearman_rho = NaN — BORDERLINE (insufficient outer seeds for Spearman computation at single
  outer seed)
- V3 trade roster Jaccard = NaN — SKIPPED (single outer seed; Jaccard requires ≥2)
- Global verdict: BORDERLINE (expected for single-seed EXPLORATION — not a flag for SPECIALIST verdict)

**Basin lottery risk:** not triggered. SPECIALIST-NEGATIVE disposition does not require multi-seed
re-validation (only PROMISING verdicts require it per `feedback_v1_basin_lottery_vigilance.md`).

---

## 10. Anomaly Notes

**(a) VOID run discovered post-launch:** the first run produced bit-identical results to /088 because
the dispatch guard was missing. The process lesson is that the banner line (`[iter-v1/NNN]`) must be
verified FIRST before any metric evaluation. Future orchestrators: check run.log line ~49 before
declaring a run valid.

**(b) IS MaxDD worsened 26.29%→41.82%:** the reshuffled replacement trades cluster in drawn-down periods
where the suppressed BTC_UP entries previously provided a defensive gap. This is consistent with the
sequential-model reshuffling degrading risk concentration, not just PnL.

**(c) OOS modest improvement (Sharpe +0.5158→+0.5952):** gate did remove losers OOS (removed WR 0.391,
replaced with WR 0.500). But the IS destruction means this is a cherry-picked positive signal from an
overall failed gate — OOS improvement does NOT override F1.

**(d) Pre-registered projection stated IS subtraction "analytically exact":** falsified. See Section 7.
The error was confusing "zero CONCURRENT overlap between existing ungated trades" with "zero sequential
replacement trades." The latter requires the gate never frees a position slot — impossible in a sequential
backtest where suppressed entries are replaced by later entries.

---

## 11. Test Outputs

- Tests: 30/30 PASS after fix commit `77947a3d`
- Lint: `uv run ruff check . && uv run ruff format .` — PASS (verified at dispatch-fix commit)
- Gate arm assertion: `lgbm.py` FAIL-LOUD assertion verified — any future `enable_btc_regime_kill=True`
  with failed index load raises `RuntimeError`

---

## 12. Verdict and BUNDLE-002 Impact

**Empirical verdict: EXPLORATION-NEGATIVE**

- F1 FAILS HARD: IS Sharpe 0.3007 vs floor 0.578 (Δ = −0.078 vs /088 vs +0.81 projected)
- F2 BELOW BAND: 18.3% IS suppression vs 20–45% band (sequential reshuffling root cause)
- The BTC-regime-kill axis for XRP is CLOSED — gate degrades IS even when properly armed
- BUNDLE-002 (`v0.v1-082`; DOT+ETH+BTC+AAVE; IS +0.72 / OOS +1.00) UNCHANGED
- XRP seat: the held UNGATED /088 PROMISING diversifier remains the best available XRP specialist
- Tag: `v0.v1-092` — EXPLORATION-NEGATIVE; axis CLOSED

---

## Status

OVERALL=READY-FOR-CRITIC

**Verdict: EXPLORATION-NEGATIVE — BTC-regime-kill axis CLOSED for XRP seat; /088 ungated SPECIALIST-PROMISING remains the XRP anchor. BUNDLE-002 (`v0.v1-082`) unchanged.**
