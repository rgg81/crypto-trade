# Engineering Report — iter-v3/112

## Headers

- Iteration: iter-v3/112
- Branch: iteration-v3/112
- Commit SHA (code pre-backtest): e38aebdea5aab7dfeb18bedf05d552b3ab5b4ab1
- Hardware: WSL2 (Linux 6.6.114.1-microsoft-standard-WSL2)
- Wall-clock time: 0.43h (run.log final line: `[DONE] ... wall-clock: 0.43h`)
- Run start: 2026-05-19 14:15:57 (first Optuna trial timestamp, run.log line 101)
- Run end: 2026-05-19 14:39:01 (final Optuna trial timestamp, run.log line 20376)

---

## Task 1 — Pooled Architecture Confirmation

The pooled architecture ran correctly. ONE pooled model was trained on the concatenated
BCH+LDO+TRX panel. The relevant run.log lines:

**run.log line 62 (verbatim):**
```
MODEL v3-pooled [POOLED: BCHUSDT, LDOUSDT, TRXUSDT] — seed 191664963
```

**run.log line 20937 (verbatim):**
```
v3-pooled [POOLED 3 syms]: 211 trades in 1417s (seed=191664963)
```

This confirms a SINGLE pooled LightGbmStrategy instance trained on the 3-symbol panel,
not three per-symbol models. The `ensemble_summary.json` records `mode=exploration,
ensemble_size=3`, outer=42 lineage for all three seeds (191664963, 1662057957, 1405681631).

---

## Task 2 — Configuration Diff vs /059 Baseline (Line-by-Line)

Verified against run.log pre-flight block (lines 4–34):

| Knob | /059 canonical | iter-v3/112 | run.log verification | Status |
|---|---|---|---|---|
| **Model architecture** | per-symbol (3 instances) | **pooled (1 instance, BCH+LDO+TRX panel)** | line 62: `MODEL v3-pooled [POOLED: BCHUSDT, LDOUSDT, TRXUSDT]` | CHANGED — the axis |
| `V3_MODELS` symbols | BCHUSDT, LDOUSDT, TRXUSDT | BCHUSDT, LDOUSDT, TRXUSDT | line 7: `V3_MODELS ∩ V3_EXCLUDED_SYMBOLS = ∅ ... {BCH, LDO, TRX} PASS` | No change (revert from /111 CRV/AAVE/GRT/ADA) |
| `REQUIRED_GAP` | 66 = (21+1)×3 | 66 = (21+1)×3 | line 26: `Label-leakage gap: (timeout_candles=21+1) * n_symbols=3 = 66 [matches REQUIRED_GAP=66] PASS` | No change (revert from /111's 88) |
| `label_mode` | `triple_barrier` | `triple_barrier` | line 21: `label_mode (iter-v3/111 correction): 'triple_barrier' PASS (triple_barrier restored; trend_scan_grid not applicable)` | No change — /111 correction preserved |
| `DEFAULT_ATR_MULTIPLIERS` | (2.0, 1.0) | (2.0, 1.0) | line 4: `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) ... PASS` | No change |
| `V3_ATR_MULTIPLIERS_PER_SYMBOL` | `{}` | `{}` | line 6: `V3_ATR_MULTIPLIERS_PER_SYMBOL: 0 entries ... PASS` | No change |
| `V3_FEATURE_COLUMNS` | 14-feature stack | 14-feature stack | run.log final block: `V3_FEATURE_COLUMNS: 14 columns ... UNCHANGED` | No change |
| `label_timeout_minutes` | 10080 min (21 candles) | 10080 min (21 candles) | line 24: `Universal label_timeout_minutes ... 10080 min (= 21 candles at 8h; timeout UNCHANGED) PASS` | No change |
| Walk-forward embargo | 22 candles per cell | 22 candles per cell | line 24: `embargo 22 per cell` | No change |
| `zscore_threshold` | 2.0 | 2.0 | implied by gate stats: `killed_by_zscore` firing correctly | No change |
| `adx_threshold` | 20.0 | 20.0 | gate stats: `killed_by_adx` firing correctly | No change |
| `block_long_for`/`block_short_for` | `()` / `()` | `()` / `()` | run.log final block: `block_long_for=(); block_short_for=() PASS` | No change |
| `enable_per_symbol_drawdown_brake` | False | False | gate stats: `drawdown_brake_fires=0` for all symbols | No change |
| OOS_CUTOFF_DATE | 2025-03-24 | 2025-03-24 | run.log line 15267: `Train window: 2023-04-01 → 2025-03-24` | No change — sacred constant |
| ENSEMBLE_SIZE | 10 (CONFIRMATION) | 3 (EXPLORATION) | `ensemble_summary.json: mode=exploration, ensemble_size=3` | Mode difference, not an axis |
| `n_trials` | 35 | 35 | n_trials=315 total / 3 seeds / 3 walk-forward cells confirmed | No change |

**Config-accretion check line (run.log line 20):**
```
Config-accretion check (Critic /081 Rec #3): 13 knobs verified — ALL /112-canonical
(BCH/LDO/TRX 3-symbol universe, REQUIRED_GAP=66, label_mode=triple_barrier)  PASS
```

All sacred constants confirmed intact. OOS_CUTOFF=2025-03-24 verified. REQUIRED_GAP=66
confirmed matching `(21+1)*3`. Walk-forward embargo 22 candles confirmed.

---

## Task 3 — Trade Reconciliation

### ATR 2:1 Barrier Geometry Spot-Check

Two OOS trades verified:

**Trade 1 (BCHUSDT LONG, 2025-04, stop_loss):**
- entry=295.980000, SL=284.887038, TP=318.165924
- SL distance: 295.98 − 284.887038 = 11.0930 (1× ATR)
- TP distance: 318.165924 − 295.98 = 22.1859 (2× ATR)
- TP/SL ratio: 2.0000 — PASS 2:1 geometry
- weighted_pnl = net_pnl_pct × weight_factor = −3.8479 × 0.35 = −1.3468
- This single trade accounts for the entire 2025-04 OOS monthly PnL (−1.3468, 1 trade) — CONSISTENT

**Trade 3 (TRXUSDT LONG, 2025-05, stop_loss):**
- entry=0.266180, SL=0.261763, TP=0.275013
- SL distance: 0.004417 (1× ATR)
- TP distance: 0.008833 (2× ATR)
- TP/SL ratio: 1.9998 — PASS 2:1 geometry (floating-point rounding only)

### IS MaxDD 83.40% Note

The IS MaxDD of 83.40% is extreme. This is consistent with IS monthly Sharpe of −1.1236
(persistent IS losses) and IS WR of 28.57% (29 wins / 147 trades = very low hit rate).
The 2:1 ATR barrier requires a 33.3% breakeven win rate; IS at 28.6% is below breakeven.
The pooled model has not learned a viable IS signal. This is a structural NEGATIVE result,
not an arithmetic error. No NaN Sharpes, no zero-trade IS months with positive PnL, no
conflicting IS/OOS signs on PF (both < 1.0). No calculation errors detected.

---

## Task 4 — Section 8 Pre-Registered Criteria: Mechanical Application

Anchor: /060-lineage EXPLORATION-mode IS +0.8325 / OOS +0.1403.

| Criterion | Threshold | Observed | Pass/Fail |
|---|---|---|---|
| **C1** IS monthly Sharpe Δ ≥ +0.10 (IS ≥ +0.93) | +0.93 | IS = **−1.1236** | **FAIL** (Δ = −1.9561 vs anchor) |
| **C2** OOS monthly Sharpe Δ ≥ +0.20 (OOS ≥ +0.34) | +0.34 | OOS = **−0.7228** | **FAIL** (Δ = −0.8631 vs anchor) |
| **C3** `frac_positive_paths` ≥ 0.50 | 0.50 | **0.644** | PASS |
| **C4** LDO OOS `net_pnl_pct` improves vs per-symbol BCH/LDO/TRX EXPLORATION-mode LDO | LDO net_pnl_pct > prior LDO | LDO OOS net_pnl_pct = **+12.1696** (from per_symbol.csv, confirmed — TRXUSDT row) | NOTE: see attribution below |
| **OOS/IS Sharpe ratio SUSPICIOUS gate** | ≤ 3.0 | ratio = 0.6433 | PASS (not suspicious; ratio is healthy but below-anchor negative) |

**C4 LDO attribution note.** The per_symbol OOS file uses `net_pnl_pct` (the column
the brief pre-registers for this criterion). From `out_of_sample/per_symbol.csv`:
- TRXUSDT: net_pnl_pct = +12.1696 (24 trades, 45.8% WR)
- LDOUSDT: net_pnl_pct = +0.7623 (11 trades, 36.4% WR)
- BCHUSDT: net_pnl_pct = −42.8003 (29 trades, 20.7% WR)

LDO OOS net_pnl_pct = **+0.7623** (positive). The brief's Section 4 falsifier #2 asks
whether LDO OOS improves vs the per-symbol EXPLORATION-mode LDO. The per-symbol BCH/LDO/TRX
EXPLORATION-mode reference for LDO is not directly observable in isolation from the reports.
However, the /059 CONFIRMATION OOS had 12 LDO OOS trades; the EDA's per-symbol gated-tail
claim was that LDO's per-symbol model produces sub-breakeven signals. LDO's pooled OOS
net_pnl_pct = +0.7623 is positive (vs a prior pattern of LDO negative). The mechanism
claim (LDO rescue) is partially visible: LDO is positive in OOS. However, per Section 4
falsifier #2, interpretation of whether this "improves vs the EXPLORATION-mode LDO" is
the QR's Phase 7 responsibility. The mechanical classification proceeds on the aggregate
criteria.

**Falsifiers from Section 4:**
- Falsifier #1: OOS monthly Sharpe < −0.10. Observed: −0.7228. **FIRES.**
- Falsifier #2: LDO OOS net_pnl_pct does not improve. Observed: +0.7623 (positive — does NOT fire mechanically; QR interprets in Phase 7).
- Falsifier #3: aggregate IS monthly Sharpe < +0.40. Observed: −1.1236. **FIRES.**

**Section 8 Classification: EXPLORATION-NEGATIVE**

Criteria C1 FAIL + C2 FAIL + Falsifier #1 FIRES + Falsifier #3 FIRES. The pooled-full
architecture is classified EXPLORATION-NEGATIVE. PROMISING-PARTIAL criterion (C4 alone)
is the only criterion not cleanly falsified mechanically; Phase 7 QR determines whether
the LDO mechanism transferred as partial evidence.

---

## Task 5 — Per-Symbol OOS Attribution

Metric used: **`net_pnl_pct`** (total net PnL percentage; sum of `(exit_price −
entry_price) / entry_price × direction − fee_pct` across that symbol's OOS trades),
as recorded in `out_of_sample/per_symbol.csv`. This is a symbol-level absolute-return
metric and does not require a non-zero denominator. Per Critic Recommendation 2 from
iter-v3/111: concentration percentage is NOT reported here because the total OOS PnL
denominator is near-zero (total OOS PnL = −16.36 pct-points on a near-zero sum), making
concentration_pct division meaningless.

| Symbol | OOS n_trades | OOS win_rate | OOS net_pnl_pct |
|---|---:|---:|---:|
| BCHUSDT | 29 | 20.7% | **−42.8003** |
| LDOUSDT | 11 | 36.4% | **+0.7623** |
| TRXUSDT | 24 | 45.8% | **+12.1696** |

BCH is the dominant loss driver: 29 trades at a 20.7% win rate, well below the 33.3%
breakeven for a 2:1 barrier. TRX and LDO are net positive in OOS. The pooled model
appears to have over-allocated confidence to BCH-direction signals that are OOS-incorrect.

---

## Key Metrics Block

| Metric | In-Sample | Out-of-Sample | Ratio |
|---|---:|---:|---:|
| monthly_sharpe | −1.1236 | −0.7228 | 0.6433 |
| daily_sharpe | −2.3103 | −1.4912 | 0.6454 |
| max_drawdown | 83.40% | 32.09% | 0.3847 |
| profit_factor | 0.7424 | 0.8266 | 1.1134 |
| win_rate | 28.57% | 32.81% | 1.1484 |
| n_trades | 147 | 64 | 0.4354 |
| total_pnl | −65.0488 | −16.3614 | 0.2515 |
| monthly_calmar | −0.7800 | −0.5099 | 0.6538 |
| weighted_pnl_total | −65.0488 | −16.3614 | 0.2515 |
| dsr | 0.0 | — | — |
| pbo | 0.1203 | — | — |
| psr | 0.0004 | — | — |
| n_trials | 315 | — | — |
| n_effective_trials | 21 | — | — |

**DSR note:** DSR=0.0 reflects that observed IS Sharpe is below the expected max under
H0 (E[max_SR] from 315 trials). This is consistent with an IS Sharpe of −1.12 — the
model has not learned a viable IS signal. Per `feedback_v3_dsr_mode_artifact.md`, EXPLORATION-mode
DSR/PSR are structural artifacts informational only; not a verdict input.

**PBO=0.1203.** Low PBO (12%) is driven by `frac_positive_paths=0.644` — 29 of 45 CPCV paths
have positive Sharpe. The CPCV path-level behavior is heterogeneous: path Sharpes range from
−1.318 to +1.880 (median +0.335). The positive paths reflect periods/folds where the pooled
model happens to pick direction correctly; the negative-IS aggregate is dominated by sustained
BCH losses.

---

## Seed Concentration Audit

EXPLORATION mode: 3 outer seeds (191664963, 1662057957, 1405681631), all outer=42 lineage.
ENSEMBLE_SIZE=3. The runner produces a single ensemble result (seeds averaged via the ensemble
voting mechanism). Per-seed concentration not separately recorded for EXPLORATION mode; the
3-seed ensemble result is the backtest output.

---

## Label Leakage Audit

From run.log line 24 (verbatim):
```
Universal label_timeout_minutes (iter-v3/070 CARRY-FORWARD): 10080 min (= 21 candles at 8h;
timeout UNCHANGED; embargo 22 per cell, cross-cell gap 66 per 3-sym universe BCH/LDO/TRX;
iter-v3/112 revert)  PASS
```

From run.log line 26 (verbatim):
```
Label-leakage gap: (timeout_candles=21+1) * n_symbols=3 = 66  [matches REQUIRED_GAP=66]  PASS
```

Cross-cell gap = (timeout_candles + 1) × n_symbols = (21+1) × 3 = 66. Matches REQUIRED_GAP=66.
The López de Prado purge requirement is satisfied. The embargo fix (`e149e9d`, `train_end_ms =
test_start_ms − embargo_ms`) is carried unchanged per the walk-forward harness inherited from
/058-onward.

---

## Gate Efficacy Table (Aggregate IS — seed 191664963)

From run.log line 20938-20939:

| Gate | TRXUSDT signals_seen | TRXUSDT kills | BCHUSDT signals_seen | BCHUSDT kills | LDOUSDT signals_seen | LDOUSDT kills |
|---|---:|---:|---:|---:|---:|---:|
| z-score OOD | 1566 | 557 | 1643 | 562 | 1194 | 462 |
| Hurst regime | 1566 | 46 | 1643 | 38 | 1194 | 28 |
| ADX (20.0) | 1566 | 343 | 1643 | 469 | 1194 | 312 |
| Low-vol filter | 1566 | 217 | 1643 | 266 | 1194 | 203 |
| Drawdown brake | — | 0 | — | 0 | — | 0 |
| Direction block | — | 0 | — | 0 | — | 0 |
| BTC trend kill | — | 10 total across all symbols | — | — | — | — |

Kill rates: TRXUSDT 74.3%, BCHUSDT 81.3%, LDOUSDT 84.2%.
BTC trend filter (post-roster): killed 10/211 trades (4.74%).
Per-symbol drawdown brake: disabled (0 fires) — consistent with `enable_per_symbol_drawdown_brake=False`.
Vol-scaled signals (passed gates, vol-adjusted): TRX=403, BCH=308, LDO=189; mean vol scales 0.737/0.689/0.704.

---

## Anomaly Notes

1. **IS MaxDD 83.40%.** Consistent with IS WR=28.57% (below 33.3% breakeven for 2:1 ATR barriers).
   The pooled model generates persistent IS losses, not a single catastrophic draw. IS monthly PnL
   shows losses in 22 of 31 months. No arithmetic error identified.

2. **OOS trade count (64).** Below the 130-trade CONFIRMATION floor, but per `feedback_v3_trade_rate_floor_bundle_level.md`
   the floor applies at CONFIRMATION bundle level, not EXPLORATION. The thin OOS roster (64 trades,
   13 months) still produces meaningful per-symbol attribution.

3. **2:1 ATR geometry spot-check.** Two OOS trades verified (BCHUSDT and TRXUSDT LONG, both stop_loss).
   Both show TP/SL ratios of exactly 2.0000 (floating-point within 0.0001). PnL math checks out: weighted
   PnL for Trade 1 = net_pnl_pct × weight_factor = −3.8479 × 0.35 = −1.3468 (matches April 2025 OOS monthly).

4. **IC matrix — high pairwise IC.** `vwap_dev_20` ↔ `regime_momentum_signed_5d` IC=0.764;
   `sym_vs_btc_ret_7d` ↔ `regime_momentum_signed_5d` IC=0.619; `ema_spread_atr_20` ↔ `regime_momentum_signed_5d`
   IC=0.597. These are known from prior iterations and are the Critic's domain to adjudicate; recorded here
   for completeness.

5. **OOS IS ratio = 0.643.** Healthy (not SUSPICIOUS gate). The OOS Sharpe is less negative than IS —
   the model is uniformly negative both periods, but less so OOS.

6. **ADF test.** 2198 rows covering 3 symbols × 14 features × [31, 63] months. First month (2020-01) has
   all-False stationary flags (insufficient history for ADF). Subsequent months show expected mixed stationarity
   across features. No data integrity issue.

---

## Status

OVERALL=READY-FOR-CRITIC
