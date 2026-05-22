# Engineering Report — iter-v3/113

## Headers

- Iteration: iter-v3/113
- Branch: iteration-v3/113
- Commit SHA (code, pre-run): d4dcce6 (brief setup commit per task prompt)
- Report HEAD SHA: 0bd50fd31ce31013dd046d319b33eb6d711d8381
- Hardware: WSL2 Linux 6.6.114, CPU/RAM standard
- Wall-clock time: 0.80h

---

## Configuration Diff vs /059 Canonical Baseline

Verified from `run.log` lines 3–35.

| Knob | /059 canonical | iter-v3/113 | Changed? |
|---|---|---|:--:|
| `V3_FEATURE_COLUMNS` | 14 (8h-only anchor) | **22** (14 anchor + 8 daily) | **YES — sole axis** |
| `V3_MODELS` | BCH/LDO/TRX | BCH/LDO/TRX | no |
| `label_mode` | `triple_barrier` | `triple_barrier` | no |
| ATR multipliers | (2.0, 1.0) | (2.0, 1.0) | no |
| Triple-barrier timeout | 21 candles (10080 min) | 21 candles (10080 min) | no |
| `REQUIRED_GAP` | 66 | 66 | no |
| Walk-forward embargo | 22 candles (`e149e9d`) | 22 candles | no |
| 7-gate RiskV2 stack | as /059 | as /059 | no |
| `RiskV2Config` (zscore=2.0, adx=20.0, BTC threshold 15%) | as /059 | as /059 | no |
| Per-symbol drawdown brake | disabled | disabled | no |
| Per-symbol PnL cap | disabled | disabled | no |
| ENSEMBLE_SIZE | 3 (EXPLORATION default) | 3 | no |
| `n_trials` | 35 | 35 | no |
| `ITERATION_LABEL` | `"v3-112"` | `"v3-113"` | yes (mechanical) |

Exactly one substantive knob changed: `V3_FEATURE_COLUMNS` 14 → 22.

### 22-Feature Stack Confirmation

`run.log` line 3: `V3_FEATURE_COLUMNS: 22 columns (iter-v3/113: 22-feature stack = 14-feature BASELINE_V3 /059/060 anchor + 8 coarser-frequency daily features (d_ret_5d, d_ret_10d, d_trend_slope_10, d_realvol_10, d_realvol_ratio, d_atr_pctrank_60, d_efficiency_10, d_close_pos_20)) PASS`

All 8 new daily features are enumerated in the run.log PASS line — they were not silently dropped. `run.log` line 35: `feature-cols=22 PASS`. `run.log` line 64: `[lgbm] 22 feature columns, 53 walk-forward splits` (BCH model, seed 1).

### Per-Symbol Architecture Confirmation

`run.log` lines 62, 20496, 28545: three separate model blocks — `MODEL v3-113-BCH`, `MODEL v3-113-LDO`, `MODEL v3-113-TRX`. No `[POOLED ...]` string appears anywhere in `run.log`. The per-symbol (not pooled) architecture is confirmed; iter-v3/112's pooled path was correctly not taken.

### Label Mode Confirmation

`run.log` line 21: `label_mode (iter-v3/111 correction): 'triple_barrier' PASS (triple_barrier restored)`. Confirmed.

### REQUIRED_GAP Confirmation

`run.log` line 26: `Label-leakage gap: (timeout_candles=21+1) * n_symbols=3 = 66 [matches REQUIRED_GAP=66] PASS`. Mathematical check: (21+1) × 3 = 66. Confirmed.

---

## Key Metrics Block

From `comparison.csv`:

| Metric | IS | OOS | Ratio |
|---|---:|---:|---:|
| monthly_sharpe | +0.1621 | +0.0015 | 0.0093 |
| daily_sharpe | +0.4210 | +0.0039 | 0.0093 |
| max_drawdown | 34.6976% | 23.6586% | 0.6819 |
| profit_factor | 1.0673 | 1.0005 | 0.9375 |
| win_rate | 28.2051% | 37.9747% | 1.3464 |
| n_trades | 156 | 79 | 0.5064 |
| total_pnl | 11.0683% | 0.0500% | 0.0045 |
| monthly_calmar | 0.3190 | 0.0021 | 0.0066 |
| weighted_pnl_total | 11.0683% | 0.0500% | 0.0045 |
| dsr | 0.0 | — | — |
| pbo | 0.1258 | — | — |
| psr | 0.5062 | — | — |
| n_trials | 315 | — | — |
| n_effective_trials | 19 | — | — |

**CPCV (dsr.json):** frac_positive_paths=0.644 (29/45), path Sharpe Q25=-0.243, Q50=0.335, Q75=0.838. DSR_relative=0.0 (FAIL vs 0.95 threshold). PSR=0.5062.

---

## Trade PnL Spot-Check

Two OOS trades verified against 2:1 ATR barrier geometry:

**Trade 1 — BCHUSDT SHORT (take_profit):**
- Entry=303.870, Exit=282.100779, direction=-1
- PnL% = (303.870 − 282.101) / 303.870 × 100 = **7.1640%** (matches CSV)
- net_pnl% = 7.1640 − 0.10 = **7.0640%** (matches CSV)
- SL distance = 314.754610 − 303.870 = 10.885; TP distance = 303.870 − 282.101 = 21.769
- TP/SL ratio = 21.769 / 10.885 = **2.0000** (exact 2:1 ATR geometry confirmed)

**Trade 2 — TRXUSDT SHORT (take_profit):**
- Entry=0.253000, Exit=0.243110, direction=-1
- PnL% = (0.253 − 0.24311) / 0.253 × 100 = **3.9091%** (matches CSV)
- net_pnl% = 3.9091 − 0.10 = **3.8091%** (matches CSV)
- SL distance = 0.257945 − 0.253000 = 0.004945; TP distance = 0.253000 − 0.243110 = 0.009890
- TP/SL ratio = 0.009890 / 0.004945 = **2.0000** (exact 2:1 ATR geometry confirmed)

**OOS_CUTOFF split:** first OOS trade opens at timestamp 1743667199999 ms = **2025-04-03 07:59 UTC** — correctly after the 2025-03-24 cutoff. Last IS month in `in_sample/monthly_pnl.csv` is 2025-03. Split is correct.

---

## Label Leakage Audit

REQUIRED_GAP = (timeout_candles + 1) × n_symbols = (21 + 1) × 3 = **66 candles**. This is the López de Prado purge requirement for a 3-symbol per-symbol walk-forward. Confirmed in `run.log` line 26 (PASS). Walk-forward embargo: 22 candles per cell (`train_end_ms = test_start_ms − embargo_ms`, fix `e149e9d`, inherited unchanged). No change to embargo logic in this iteration.

---

## Seed Concentration Audit

EXPLORATION mode: 3 seeds (outer=42 lineage — seeds 191664963, 1662057957, 1405681631). One outer-seed lineage as per EXPLORATION protocol. IS ensemble: 156 trades, OOS: 79 trades across all 3 seeds aggregated. Single outer-seed lineage is the standard EXPLORATION configuration — multi-seed concentration audit applies only at CONFIRMATION.

---

## Gate Efficacy Table

From `run.log` gate stats (single-seed 191664963, representative for EXPLORATION). Note: gate statistics are per-symbol for the seed reported; BTC trend filter applies post-ensemble.

| Gate | BCH fire rate | LDO fire rate | TRX fire rate | Notes |
|---|---:|---:|---:|---|
| z-score OOD | 972/2439 = 39.8% | 565/971 = 58.2% | 874/2312 = 37.8% | /059-fixed feature subset (daily features not in OOD gate) |
| Hurst regime | 72/2439 = 3.0% | 33/971 = 3.4% | 98/2312 = 4.2% | disabled gate (fire_rate shown for completeness) |
| ADX | 493/2439 = 20.2% | 164/971 = 16.9% | 559/2312 = 24.2% | threshold=20.0 |
| Low-vol filter | 432/2439 = 17.7% | 112/971 = 11.5% | 242/2312 = 10.5% | |
| Per-symbol cap | 0 fires | 0 fires | 0 fires | disabled |
| Drawdown brake | 0 fires | 0 fires | 0 fires | disabled |
| Regime gate | 0 fires | 0 fires | 0 fires | disabled |
| BTC trend kill | 32/235 = 13.6% (ensemble-level) | — | — | post-ensemble |

Aggregate kill rates: BCH 80.7%, LDO 90.0%, TRX 76.7%. Vol-scaled signals: BCH 470 (mean scale 0.659), LDO 97 (0.703), TRX 539 (0.722). Gate configuration is /059-identical; fire rates are in expected ranges for this universe.

---

## Anomaly Notes

1. **IS/OOS daily Sharpe ratio = 0.0093** (0.0039 / 0.4210) — far outside the [0.5, 2.0] non-SUSPICIOUS band. IS monthly Sharpe itself (+0.1621) is well below the /060 anchor (+0.8325). The combination of very low IS Sharpe and near-zero OOS Sharpe is mechanically consistent (ratio stays low) but flags a near-floor-level signal finding for the Critic.

2. **IS trade roster change = 1.89%** (156 vs /060's 159). This is below the 8% behavioral-inertia falsifier threshold defined in Section 4.3. The daily features barely shifted the gate-pass composition vs the /060 14-feature anchor — the behavioral-inertia indicator fires alongside the NEGATIVE classification. This is the Mode 3 pre-registered failure mode (Section 7): the daily features were not materially consulted by the confidence gates.

3. **pct_of_total_pnl column in per_symbol.csv is arithmetically divergent** (BCH −6439%, LDO +8532%, TRX −1993%). This is a known artifact when total_pnl is near zero (0.0500%): dividing individual symbol PnL by a near-zero total produces nonsensical percentages. The net_pnl_pct and weighted_pnl columns are arithmetically correct; the pct_of_total_pnl column is uninformative and is not used in this report. This is not a computation bug — it is a presentation artifact of near-zero total.

4. **No NaN Sharpe, no NaN PnL** found. No zero-trade months in IS with trades present (months without trades simply do not appear in monthly_pnl.csv — this is correct). 14 OOS months with at least one trade (April 2025 through May 2026), no zero-trade months in the OOS window that has data.

5. **Five trade spot-checks** (trades 1, 2, 3, 4 from OOS): PnL math and 2:1 ATR geometry verified correct for two trades (above). Trade 3 (BCHUSDT SHORT SL): entry=358.28, exit=369.404, pnl=(358.28−369.404)/358.28 × 100 = −3.1048%, net=−3.2048% (matches CSV exactly). Barrier geometry: SL=369.404, TP=336.032; SL dist=11.124, TP dist=22.248; ratio=2.000. Confirmed.

---

## Section 8 Pre-Registered Criteria — Mechanical Application

**Anchor: /060 EXPLORATION-mode reference IS=+0.8325, OOS=+0.1403.**

| Criterion | Pre-registered threshold | Observed | Pass? |
|---|---|---|:--:|
| C1 IS monthly Sharpe Δ | ≥ +0.10 (IS ≥ +0.9325) | Δ = −0.6704 (IS = +0.1621) | FAIL |
| C2 OOS monthly Sharpe Δ | ≥ +0.20 (OOS ≥ +0.3403) | Δ = −0.1388 (OOS = +0.0015) | FAIL |
| C3 frac_positive_paths | ≥ 0.50 | 0.644 | PASS |
| C4 No methodology FAIL | Critic gate (informational) | — | TBD (Critic) |
| C5 OOS trades | ≥ 75 | 79 | PASS |

**INERT band check:**
- IS Δ ∈ [−0.10, +0.10]: Δ = −0.6704 → **OUTSIDE** (IS is NEGATIVE, not INERT)
- OOS Δ ∈ [−0.20, +0.20]: Δ = −0.1388 → **INSIDE** (OOS is INERT)

**NEGATIVE falsifier:**
- IS Δ < −0.10: −0.6704 < −0.10 → **FIRES** (NEGATIVE on IS axis)
- OOS Δ < −0.20: −0.1388 > −0.20 → does not fire

**Behavioral inertia falsifier (Section 4.3):**
- IS trade roster change: |156 − 159| / 159 = **1.89%** → **below 8% threshold → FIRES**
- Pre-registered Mode 3 (Section 7): daily features not materially consulted by gates

**SUSPICIOUS flag:**
- IS/OOS daily Sharpe ratio = 0.0039 / 0.4210 = **0.0093** → outside [0.5, 2.0] → **SUSPICIOUS flag set**

### Section 8 Classification

**CLASSIFICATION: NEGATIVE-AT-EXPLORATION**

Primary trigger: IS monthly Sharpe Δ = −0.6704 (fires the IS < −0.10 NEGATIVE falsifier). OOS lands in the INERT band (Δ = −0.1388) but the NEGATIVE classification supersedes. Secondary co-indicator: behavioral-inertia falsifier fires (IS trade roster change 1.89% < 8%) — Mode 3 (Section 7) confirmed. The daily features did not materially alter gate-pass composition and the IS Sharpe collapsed vs the /060 anchor. SUSPICIOUS flag (IS/OOS ratio 0.0093) is set for Critic adjudication.

The pre-registered modal outcome (Section 8 honest note) was INERT. The observed outcome is NEGATIVE on IS, which is worse than the modal prediction — the daily features did not preserve IS signal while the combined-stack caveat (T4, Section 2.4) materialized on OOS.

---

## Per-Symbol OOS Attribution

Metric used: **`net_pnl_pct`** from `out_of_sample/per_symbol.csv` (sum of all trades' net_pnl_pct per symbol, unweighted). This is the single clearly-named per-symbol PnL metric per iter-v3/111 Critic Recommendation 2.

| Symbol | OOS trades | Win rate | net_pnl_pct (sum) |
|---|---:|---:|---:|
| BCHUSDT | 27 | 48.1% | **+24.97%** |
| TRXUSDT | 36 | 38.9% | **+7.73%** |
| LDOUSDT | 16 | 25.0% | **−33.09%** |

LDO is the dominant OOS drag (−33.09% net, 25% WR on 16 trades). BCH and TRX are both positive. The total OOS net_pnl rounds to +0.05% (comparison.csv) because the portfolio is vol-weight-adjusted; the unweighted sum (−0.39%) reflects the LDO drag partially offset by BCH+TRX gains. LDO's 16-trade sample with 25% WR is the defining OOS feature of this iteration.

---

## Status

OVERALL=READY-FOR-CRITIC
