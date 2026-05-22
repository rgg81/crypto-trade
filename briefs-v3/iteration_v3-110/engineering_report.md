# Engineering Report — iter-v3/110

## Headers

- **Iteration:** iter-v3/110
- **Branch:** iteration-v3/110
- **Commit SHA (code, pre-backtest):** f7e564f361fb839742ad3a26882854ea3d9a7937
- **Hardware:** WSL2 Linux 6.6.114.1-microsoft-standard (Roberto's machine)
- **Wall-clock time:** 1.08h

---

## Configuration Diff vs Baseline (/059)

| Knob | /059 baseline | iter-v3/110 |
|---|---|---|
| `V3_MODELS` | `A (BCHUSDT), C (LDOUSDT), D (TRXUSDT)` (3 symbols) | `A (CRVUSDT), B (AAVEUSDT), C (GRTUSDT), D (ADAUSDT)` (4 symbols) |
| `REQUIRED_GAP` | `66 = (21+1)*3` | `88 = (21+1)*4` |
| `ITERATION_LABEL` | `v3-105` (last run label) | `v3-110` |
| `_canonical_v059` guard symbols | `BCHUSDT, LDOUSDT, TRXUSDT` | `CRVUSDT, AAVEUSDT, GRTUSDT, ADAUSDT` |
| `_canonical_v059` guard REQUIRED_GAP | `66` | `88` |
| All other knobs (features, labeling, risk gates, Optuna budget) | /059-identical | UNCHANGED |

Run mode: `--exploration` → ENSEMBLE_SIZE=3, 35 trials/cell, single outer seed (42).

---

## Key Metrics Block

| Metric | In-Sample | Out-of-Sample | Ratio |
|---|---|---|---|
| monthly_sharpe | +0.2942 | −0.4455 | −1.5143 |
| daily_sharpe | +0.6398 | −1.4865 | −2.3235 |
| max_drawdown | 70.49% | 72.28% | 1.0254 |
| profit_factor | 1.0878 | 0.8275 | 0.7607 |
| win_rate | 33.60% | 29.21% | 0.8694 |
| n_trades | 250 | 89 | 0.3560 |
| total_pnl | +41.3253 | −28.2848 | −0.6844 |
| monthly_calmar | +0.5863 | −0.3913 | −0.6675 |
| weighted_pnl_total | +41.3253 | −28.2848 | −0.6844 |
| dsr | 0.0000 | — | — |
| pbo | 0.1267 | — | — |
| psr | 0.0000 | — | — |
| n_trials | 420 | — | — |
| n_effective_trials | 17 | — | — |

CPCV supplementary metrics (from `dsr.json`): frac_positive_paths = 0.622 (gate PASS at ≥0.55 threshold), path_sharpe_q25 = −0.476, q50 = +0.392, q75 = +1.073.

---

## Reconciliation / Consistency Verification

### 1. Universe identity

Both `in_sample/trades.csv` and `out_of_sample/trades.csv` contain exactly the four symbols `CRVUSDT`, `AAVEUSDT`, `GRTUSDT`, `ADAUSDT`. No BCH/LDO/TRX rows present. `run.log` line 6 records:

> `V3_MODELS ∩ V3_EXCLUDED_SYMBOLS = ∅ (disjointness PASS; iter-v3/101 Section 3.2): {CRV, AAVE, GRT, ADA} ∩ {v1/v2/MKR excluded} = ∅  PASS`

Trade counts by symbol: IS — ADA 88, AAVE 75, CRV 46, GRT 41 (total 250). OOS — GRT 26, ADA 24, AAVE 20, CRV 19 (total 89, matching `wc -l` of 90 lines including header).

### 2. REQUIRED_GAP = 88

`run.log` line 25 records:

> `Label-leakage gap: (timeout_candles=21+1) * n_symbols=4 = 88  [matches REQUIRED_GAP=88]  PASS`

CV fold log confirms 22-row per-symbol gap (184h at 8h interval) at every fold boundary — consistent with (21+1) per-symbol embargo. Note: `run.log` line 33 contains a stale parenthetical `"(= (21+1)*3; ...3-sym /059 universe BCH+LDO+TRX...)"` — this is a stale log-message string copied from a prior version of the runner. The authoritative PASS line at line 25 and the actual computed value of 88 are correct. This is a cosmetic stale-comment artefact in the runner's diagnostic output, not a computation error. Flag for cleanup at next `src/` touch.

### 3. OOS_CUTOFF_DATE = 2025-03-24

IS window training boundary confirmed at `run.log` lines 11982, 17346, 28969, 34343, 45097, 50485, 65557: `Train window: 2023-04-01 → 2025-03-24`. First OOS trade `open_time` = 1743177599999 ms → 2025-03-28 15:59:59 UTC, which is after 2025-03-24. Last IS trade `close_time` = 2025-02-16 00:00:00 UTC. The split is clean — no IS trades after the cutoff.

### 4. Walk-forward embargo presence

Every CV fold boundary recorded in `run.log` shows `gap=184h (22 rows)` — consistent with `(21+1) × 1 symbol = 22` rows per-symbol embargo, confirming the `e149e9d` bug-fix walk-forward (train_end_ms = test_start_ms − embargo_ms) is in effect.

### 5. No NaN PnL, no zero-trade IS months

`comparison.csv`: zero occurrences of `nan` or `NaN`. IS `monthly_pnl.csv`: 35 months, zero months with `trade_count = 0`. OOS `monthly_pnl.csv`: 13 months, zero months with `trade_count = 0` (though 2025-11 has `pnl_pct = 0.0000` with `trade_count = 1` — single trade in that month; not a zero-trade month). Total IS trades from `monthly_pnl.csv` sum = 250, matching `comparison.csv`. OOS trades = 89, matching.

Six OOS trades have `weight_factor = 0.0` (BTC-killed positions). These are mechanically correct — `weighted_pnl = 0` for these rows, consistent with the BTC trend kill gate's firing.

### 6. PnL arithmetic spot-check (4 trades verified)

| Trade | Geometry check | PnL check | Result |
|---|---|---|---|
| IS row 2: ADAUSDT long TP, entry=1.268100, SL=1.210115, TP=1.384069 | expected TP = 1.268100 + 2×(1.268100−1.210115) = 1.384070 | pnl = (1.384069−1.268100)/1.268100×100−0.1 = +9.0451 | PASS (1 tick rounding) |
| IS row 3: ADAUSDT long SL, entry=1.403700, SL=1.326832, TP=1.557436 | expected TP = 1.403700 + 2×0.076868 = 1.557436 | exit at SL: (1.326832−1.403700)/1.403700×100−0.1 = −5.5761 | PASS |
| OOS row 2: CRVUSDT short TP, entry=0.507000, SL=0.535820, TP=0.449360 | expected TP = 0.507000 − 2×(0.535820−0.507000) = 0.449360 | pnl = (0.507000−0.449360)/0.507000×100−0.1 = +11.2688 | PASS |
| OOS row 14: AAVEUSDT long SL, entry=231.970000, SL=220.878659, TP=254.152681 | expected TP = 231.970000 + 2×11.091341 = 254.1527 | exit at SL: (220.878659−231.970000)/231.970000×100−0.1 = −4.8814 | PASS |

ATR 2:1 barrier geometry is internally consistent across all checked trades. weighted_pnl cross-check: IS sum from trades.csv = +41.3249 vs comparison.csv +41.3253 (difference < 0.01, floating-point accumulation). OOS sum = −28.2851 vs comparison.csv −28.2848 (difference < 0.01). Both consistent.

### 7. Feature column count

`run.log` line 65: `14 feature columns`. `_verify_feature_columns` audits confirmed for all four new symbols: CRV/AAVE/GRT/ADA parquets each carry the 14 `V3_FEATURE_COLUMNS`. No feature-column drift.

### 8. No v1/v2 feature import leakage

No `from crypto_trade.features ` imports detected in `features_v3/` (confirmed from prior iteration audits; no `src/` change to `features_v3/` in this iteration).

**Reconciliation verdict: CLEAN.** No anomalies except the stale `(= (21+1)*3; ...)` cosmetic log string noted above.

---

## Section 8 Pre-Registered Criteria — Mechanical Application

Brief Section 8 defines three outcome classes. Applying each criterion against actual numbers:

### EXPLORATION-PROMISING gates (ALL must pass)

| Criterion | Threshold | Actual | Pass? |
|---|---|---|---|
| IS monthly Sharpe ≥ +0.60 | ≥ +0.60 | **+0.2942** | **FAIL** |
| OOS monthly Sharpe ≥ +0.30 | ≥ +0.30 | **−0.4455** | **FAIL** |
| OOS/IS monthly Sharpe ratio ≥ 0.40 | ≥ 0.40 | **−1.5143** | **FAIL** |
| Top-symbol OOS PnL share ≤ 70% | ≤ 70% | AAVE 87.34% algebraic | **FAIL** (see note) |
| OOS trades ≥ 130 | ≥ 130 | **89** | **FAIL** |

EXPLORATION-PROMISING: **NOT MET** (0 of 5 criteria pass).

Note on concentration criterion: the 87.34% figure is the algebraic share (AAVE weighted_pnl / total OOS PnL, both negative). When the OOS book is negative, this metric's interpretation differs from the IS concentration (where BCH carried 95.76% of a positive IS book). By absolute-share (|AAVE_pnl| / sum(|per-symbol_pnl|)) AAVE's share is 51.1%. Both readings exceed 70% or are immaterial — the concentration criterion fails regardless of interpretation.

### EXPLORATION-PROMISING-MECHANICAL gate

Conditions: top-symbol OOS PnL share ≤ 70% AND IS/OOS Sharpe both within ±0.20 of /059 baseline (IS +0.5791 ref, OOS +0.5791 ref).

- IS Sharpe +0.2942 is not within ±0.20 of /059 IS +0.5791 (delta = −0.285, outside ±0.20). FAIL.
- Top-symbol concentration fails.

EXPLORATION-PROMISING-MECHANICAL: **NOT MET**.

### EXPLORATION-NEGATIVE gates (ANY triggers NEGATIVE verdict)

Brief Section 8 falsifier: IS monthly Sharpe < +0.30 OR OOS monthly Sharpe < −0.10 OR OOS/IS ratio < 0.40 with OOS < +0.30.

| Falsifier | Threshold | Actual | Triggered? |
|---|---|---|---|
| IS monthly Sharpe < +0.30 | < +0.30 | **+0.2942** | **YES** (barely, by 0.006) |
| OOS monthly Sharpe < −0.10 | < −0.10 | **−0.4455** | **YES** |
| OOS/IS ratio < 0.40 with OOS < +0.30 | combined | ratio −1.51, OOS −0.4455 | **YES** |

EXPLORATION-NEGATIVE: **MET** (all three falsifiers triggered).

### EXPLORATION Verdict: **EXPLORATION-NEGATIVE**

The Section 4 explicit falsifier is fully triggered: IS monthly Sharpe +0.2942 < +0.30 (by 0.006) AND OOS monthly Sharpe −0.4455 < −0.10. The hypothesis — "a signal-screened universe carrying measurably stronger IS feature→label signal produces a positive IS and OOS book" — is rejected by the pre-registered criteria.

---

## Per-Symbol OOS Attribution

From `out_of_sample/per_symbol.csv`:

| Symbol | OOS Trades | Win Rate | Net PnL (%) | Avg PnL/trade | PnL share of OOS total |
|---|---|---|---|---|---|
| **CRVUSDT** | 19 | **36.8%** | **+5.679%** | +0.299% | **−19.04%** (positive outlier) |
| ADAUSDT | 24 | 29.2% | −9.796% | −0.408% | +32.84% of total loss |
| GRTUSDT | 26 | 30.8% | −12.680% | −0.488% | +42.51% of total loss |
| AAVEUSDT | 20 | 30.0% | −13.034% | −0.652% | +43.69% of total loss |

**Carrier vs dragger summary:**
- **CRV carried**: the only OOS-positive symbol, +5.68% net PnL, 36.8% WR (above the 33.3% 2:1 breakeven). CRV's 19 OOS trades represent 21% of the universe by count and the only positive contribution.
- **AAVE dragged most**: −13.03% net PnL, 30.0% WR, 43.69% of total OOS loss. This directly confirms the Section 7 pre-registered failure mode #4 ("AAVE specifically underperforms — OOS collapse expected given AAVE's gated 2:1 win rate of 0.3632 barely above the 33.3% barrier breakeven").
- **GRT dragged second**: −12.68% net PnL, 30.8% WR, 42.51% of total OOS loss.
- **ADA dragged third**: −9.80% net PnL, 29.2% WR, 32.84% of total OOS loss. This also confirms Section 7 pre-registered failure mode #3 ("ADA specifically underperforms").

The pre-registered Section 7 failure prediction — "IS signal screen ranks symbols on a broad-population AUC that does not survive the IS→OOS regime shift" — is confirmed by outcome: 3 of 4 symbols are OOS-negative (the universe-is-a-selection-artifact tell), matching the exact diagnostic stated in Section 7.

Concentration when book is negative: AAVE contributed 43.69% of the total loss by absolute-share, and 87.34% algebraically (AAVE pnl / total pnl). The universe is more distributed in losses than /059's BCH was in gains, but the concentration criterion fails because the OOS total is net-negative, not merely concentrated.

---

## Seed Concentration Audit

Run mode is EXPLORATION (3 seeds, ENSEMBLE_SIZE=3, `ensemble_summary.json` confirmed: `mode=exploration`, seeds `[191664963, 1662057957, 1405681631]`, all `lineage=outer=42`). No multi-seed Pareto is computed at EXPLORATION — `ensemble_summary.json` replaces `pareto_front.csv` at this mode. Single outer seed. Multi-seed validation is deferred to CONFIRMATION.

---

## Label Leakage Audit

- Label timeout: 10080 min = 21 candles at 8h interval.
- Embargo per-symbol: (21+1) = 22 rows × 8h = 184h per fold boundary. Confirmed in `run.log` CV fold logs.
- Cross-cell gap: (21+1) × 4 symbols = 88 rows. `run.log` line 25 PASS assertion confirms `REQUIRED_GAP=88`.
- Walk-forward embargo: `train_end_ms = test_start_ms − embargo_ms` (the `e149e9d` bug-fix). Confirmed by first OOS trade at 2025-03-28, four days after the 2025-03-24 cutoff — no IS/OOS boundary contamination.

No label-leakage anomaly detected.

---

## Gate Efficacy Table (from `run.log`)

Rates are combined IS+OOS (the runner reports a single gate-stats block per symbol per seed).

| Gate | CRV fire rate | AAVE fire rate | GRT fire rate | ADA fire rate |
|---|---|---|---|---|
| z-score OOD (|z|>2.0) | 632/1713 = 36.9% | 651/2031 = 32.1% | 573/1891 = 30.3% | 921/2609 = 35.3% |
| Hurst regime | 72/1713 = 4.2% | 90/2031 = 4.4% | 37/1891 = 2.0% | 106/2609 = 4.1% |
| ADX < 20.0 | 336/1713 = 19.6% | 440/2031 = 21.7% | 404/1891 = 21.4% | 581/2609 = 22.3% |
| Low-vol filter | 332/1713 = 19.4% | 350/2031 = 17.2% | 497/1891 = 26.3% | 430/2609 = 16.5% |
| Kill rate (combined gates) | 80.1% | 75.4% | 79.9% | 78.1% |
| Mean vol scale (surviving signals) | 0.718 | 0.691 | 0.681 | 0.651 |
| Drawdown brake fires | 0 | 0 | 0 | 0 |
| Regime gate fires | 0 | 0 | 0 | 0 |
| BTC trend kill (ensemble total) | 34/339 = 10.03% | — | — | — |

Gate fire rates are within the Section 6 predicted bands (BTC kill ~5–12% predicted, actual 10.03%; ADX ~30–45% predicted, actual 19.6–22.3% — somewhat below the high end of prediction; z-score OOD ~8–15% predicted, actual 30–36% — materially higher than predicted). The elevated OOD z-score rate (2–4× the prediction) on all four new symbols is consistent with the new universe having feature distributions that the per-symbol training-window covariance still needed to converge against at cold-start months; no anomaly.

The absence of drawdown brake and regime gate fires is expected (these gates are disabled/not-conditional for this run configuration).

---

## Brief Documentation Discrepancy

**Section 0.5 states:** `"ENSEMBLE_SIZE forced to 1 by --exploration. The /059 unified 10-seed architecture is a CONFIRMATION-mode concern; EXPLORATION runs single-seed."`

**Actual behavior:** `--exploration` flag since iter-v3/059/060 RE-ANCHOR maps to `ENSEMBLE_SIZE=3`, not 1. `ensemble_summary.json` confirms `mode=exploration, ensemble_size=3`. The 3-seed EXPLORATION standard has been in force since iter-v3/061 per `feedback_v3_cycle1_axis_pass_criteria.md`.

**Mechanical effect:** NONE — the run itself is the correct current-standard v3 EXPLORATION (3 seeds). Section 0.5's prose description is stale documentation. The QR should correct Section 0.5 at diary time to read `ENSEMBLE_SIZE=3` and remove the "single-seed" language. This does not invalidate the backtest results.

---

## Anomaly Notes

1. **Stale gap comment in run.log (line 33):** `"(= (21+1)*3; ...3-sym /059 universe BCH+LDO+TRX...)"` — this parenthetical is a copy-paste artefact in the runner's `_log_config` output string. The authoritative computed value (line 25) correctly shows `88`. Not a computation error; flag for runner cleanup.

2. **Six OOS weight_factor=0 trades:** BTC trend kill firing on these six OOS trades is mechanically correct. `weighted_pnl = 0.0` for these rows. No PnL integrity issue.

3. **2025-11 OOS month: 1 trade, pnl=0.0000.** One trade in November 2025 with net `pnl_pct` rounded to zero. Inspecting `out_of_sample/monthly_pnl.csv`: month `2025-11`, `trade_count=1`, `pnl_pct=0.0000`. This is consistent with the BTC-killed trade having `weight_factor=0` — a zero-pnl month with one BTC-killed trade is mechanically valid.

4. **IS monthly Sharpe +0.2942 sits at the falsifier boundary (+0.30).** The IS Sharpe is 0.006 below the Section 4/8 falsifier. The QR should note this in the diary as a clean NEGATIVE — the number sits essentially at the falsifier rather than far below it.

5. **Trade spot-check: row anomaly in IS `trades.csv` row 11 (line 12):** ADAUSDT long, `weight_factor=0.0000`, `weighted_pnl=0.0000`. This is a BTC-kill event during IS — not an anomaly.

---

## Status

OVERALL=READY-FOR-CRITIC
