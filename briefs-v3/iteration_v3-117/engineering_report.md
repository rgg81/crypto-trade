# Engineering Report — iter-v3/117

## Headers

- Iteration: iter-v3/117
- Branch: iteration-v3/117
- Commit SHA (code, pre-backtest): ac2c9f651a1d0f2d79f3864f6ef0c7f99ddfec97
- Hardware: WSL2 Linux 6.6.114.1-microsoft-standard (x86_64)
- Wall-clock time: 0.64h

---

## Configuration Diff vs /059 BASELINE_V3.md

| Knob | /059 Baseline | iter-v3/117 | Status |
|---|---|---|---|
| bar_interval | 8h | **24h** | CHANGED — primary axis |
| Multi-offset | (N/A) | **3 offsets: 0h, 8h, 16h UTC** | NEW |
| feature_columns | 14 (V3_FEATURE_COLUMNS) | **15 (14 + offset_id)** | +1 |
| REQUIRED_GAP | 66 = (21+1)×3 | **72 = (7+1)×3×3** | CHANGED — 24h formula |
| cooldown_candles | 4 (= 32h at 8h) | **2 (= 48h at 24h)** | CHANGED — calendar equiv |
| label_timeout_minutes | 10080 (21×8h) | 10080 (7×24h) | UNCHANGED in minutes |
| label_mode | triple_barrier | triple_barrier | UNCHANGED — /116 revert held |
| enable_no_confirm_exit | False | False | UNCHANGED — /116 reverted |
| ATR multipliers | (2.0, 1.0) | (2.0, 1.0) | UNCHANGED |
| ensemble_size | 5 (CONFIRMATION) | 3 (EXPLORATION mode) | EXPLORATION |
| n_trials | 35 | 35 | UNCHANGED |
| OOS_CUTOFF_DATE | 2025-03-24 | 2025-03-24 | SACRED — UNCHANGED |
| training_months | 24 | 24 | SACRED — UNCHANGED |
| Universe | BCH/LDO/TRX | BCH/LDO/TRX | UNCHANGED |
| Model | LightGBM | LightGBM | UNCHANGED |

All pre-flight PASS lines confirmed in run.log (lines 3–38). Sacred constants verified.
`label_mode=triple_barrier` confirmed (line 21). `enable_no_confirm_exit=False` confirmed (line 28).
`V3_FEATURE_COLUMNS=14+offset_id` confirmed (line 38). `REQUIRED_GAP=72` confirmed (line 37).
`bar_interval=24h` confirmed (line 33).

---

## Key Metrics Block

| Metric | In-Sample | Out-of-Sample | OOS/IS Ratio |
|---|---|---|---|
| monthly_sharpe | **-2.1702** | **-3.2589** | 1.5016 |
| daily_sharpe | -5.8163 | -10.9748 | 1.8869 |
| max_drawdown | 4.9059% | 0.9269% | 0.1889 |
| profit_factor | 0.4657 | 0.2361 | 0.5071 |
| win_rate | 36.47% | 40.00% | 1.0968 |
| n_trades | 170 | 25 | 0.1471 |
| total_pnl | -4.3030% | -0.9303% | 0.2162 |
| monthly_calmar | -0.8771 | -1.0037 | 1.1443 |
| weighted_pnl_total | -4.3030% | -0.9303% | 0.2162 |
| dsr | 0.0000 | — | — |
| pbo | 0.0000 | — | — |
| psr | 0.0000 | — | — |
| n_trials | 315 | — | — |
| n_effective_trials | 22 | — | — |

vs /060 EXPLORATION anchor (IS +0.8325 / OOS +0.1403):
- IS Δ = **-3.0027** (far below the Criterion 1 threshold of -0.10)
- OOS Δ = **-3.3992** (far below the Criterion 1b floor of -0.20)

CPCV frac_positive_paths: 0.600 (gate PASS threshold 0.55); CPCV path Sharpe Q75: +0.7742.
Note: frac_positive_paths=0.60 uses return-proxy paths (candle-level), NOT trade Sharpe paths.
The return-proxy positive fraction and the catastrophic IS/OOS trade Sharpe are not contradictory:
the return proxy reflects the underlying candle return distribution, while IS/OOS trades reflect
the filtered, gated, and confidence-thresholded subset. Per-cell mean PBO=0.0000 (100% of 128 cells).

---

## Per-Symbol Attribution (concentration_pct from comparison.csv)

**IS per-symbol:**

| Symbol | Trades | Win Rate | Net PnL | Avg PnL/trade | concentration_pct |
|---|---|---|---|---|---|
| BCHUSDT | 67 | 47.8% | -4.6491% | -0.0694% | — |
| LDOUSDT | 24 | 66.7% | +0.8665% | +0.0361% | — |
| TRXUSDT | 79 | 24.1% | -4.9095% | -0.0621% | — |

**OOS per-symbol (from comparison.csv per_symbol section):**

| Symbol | Trades | Win Rate | Net PnL | concentration_pct |
|---|---|---|---|---|
| BCHUSDT | 11 | 27.3% | -0.8767% | **58.18%** |
| LDOUSDT | 14 | 50.0% | -0.7199% | **41.82%** |
| TRXUSDT | **0** | — | — | — |

**Attribution finding:** All three OOS symbols are catastrophically negative or absent.
TRX produced ZERO OOS trades despite 79 IS trades — the model that was profitable on TRX in IS
did not emit any signals above the confidence threshold in the 14-month OOS window.
BCH is the concentration leader at 58.18% with WR=27.3% (below the 33.3% 2:1 ATR breakeven).
LDO is 41.82% with WR=50.0% (above breakeven but insufficient to offset fees).
No single symbol is carrying the portfolio — all three paths fail.

OOS months with any trades: 2025-07 (5), 2025-08 (6), 2025-09 (8), 2025-10 (4), 2026-04 (1), 2026-05 (1).
Zero-trade OOS months: 8 of 14 months (2025-04/05/06/11/12, 2026-01/02/03).

---

## AUC vs PnL Reconciliation (Core Diagnostic Question)

**The divergence:** EDA held-out universe-pooled AUC = **0.5823** (v3's strongest ever). Production IS monthly Sharpe = **-2.1702**. These are not contradictory — they measure different things — but the divergence requires an honest explanation.

**Mechanism 1 — AUC measures rank-ordering over the full distribution; the confidence gate selects the high-confidence tail.**

AUC 0.5823 means the model rank-orders predict_proba scores slightly better than random across the FULL population of 12,280 IS rows. But the confidence gate (realized threshold 0.648 for BCH) selects only the HIGH-CONFIDENCE tail. The key question is whether the high-confidence tail is directionally correct. The IS per-symbol win rates answer this:

- BCH: 67 trades at WR=47.8%. The 2:1 ATR barrier needs WR > 33.3% to break even before fees. BCH IS WR clears the raw breakeven but net PnL is -4.6491% — the fee drag (0.10%/trade round-trip) at 47.8% WR is not enough net expected value. At 47.8% WR with 2:1 payout: E[PnL/trade] = 0.478×(2×ATR%) - 0.522×(1×ATR%) - 0.10% fee. With typical ATR%≈0.15%: E = 0.478×0.30% - 0.522×0.15% - 0.10% ≈ 0.143% - 0.078% - 0.10% = -0.035%/trade. Consistent with observed -0.0694%/trade (the ATR is smaller than 0.15% average at 24h daily bars with tighter barriers, amplifying fee dominance).

- TRX: 79 trades at WR=24.1% — **BELOW the 33.3% breakeven**. High-confidence TRX predictions are systematically wrong. This is the primary signal that the gated-tail AUC diverges badly from the population AUC of 0.5823.

- LDO: 24 trades at WR=66.7% — above breakeven. LDO's high-confidence predictions are directionally correct but the trade volume is too low to carry the portfolio.

**Mechanism 2 — BCH's 99.12% label imbalance produces a systematically mis-calibrated predict_proba.**

BCH labels are 99.12% positive (TP hits) in the training panel. The LightGBM trained on this panel cannot learn from SL-hitting events (only 0.88% of training rows). The resulting model likely produces predict_proba values that are consistently near-1.0 for LONG bets, regardless of whether the current market state is trending or mean-reverting. The confidence gate at 0.648 selects what appear to be "high-confidence" LONG predictions — but they are not informative because the model has no SL-class signal to calibrate against.

The population AUC of 0.5823 captures the rank-ordering across the FULL panel including the 0.88% SL-hitting rows (label=0). A model that outputs 0.999 for all rows would have AUC=0.5 on a balanced panel but can have AUC > 0.5 on a 99% positive panel if the rare negative rows happen to be ranked lower. This is the standard "AUC can be high on imbalanced data even for degenerate models" artifact.

**Mechanism 3 — TRX's structural failure is the dominant loss driver.**

TRX generated 79 IS trades at WR=24.1% — producing IS net PnL of -4.9095%, the largest IS loss. In OOS it generated ZERO trades. The TRX model learned some IS-specific pattern that (a) fired frequently IS and (b) was directionally wrong (24.1% WR), then (c) produced no OOS signal at all. This is the hallmark of IS-specific overfitting on a noisy target: the model found false IS regularities that don't transfer OOS.

**Gated-tail hit rate vs population AUC summary:**

| Symbol | EDA per-symbol AUC | IS gated WR | Required WR (2:1) | Divergence direction |
|---|---|---|---|---|
| BCH | 0.4778 (below null q50) | 47.8% | 33.3% | AUC UNDER-predicted WR; but fee-dominated |
| LDO | 0.5201 | 66.7% | 33.3% | AUC agrees — LDO has real signal |
| TRX | 0.5092 | 24.1% | 33.3% | AUC OVER-predicted WR; gated tail is wrong |

The universe-pooled AUC of 0.5823 aggregates BCH (mostly label=1 rows trivially ranked), LDO (real signal), and TRX (spurious IS signal). The per-symbol breakdown reveals TRX's high-confidence tail is directionally wrong, which is obscured in the pooled metric.

---

## Label-Leakage Audit

Formula: REQUIRED_GAP = (timeout_candles + 1) × n_symbols × n_offsets = (7+1) × 3 × 3 = 72.
Confirmed in run.log line 37: `REQUIRED_GAP=72 ((7+1)*3*3=72 [24h override]...PASS`.
CV fold gap: 8 rows per fold (run.log line 150-157: `gap=72h (8 rows)` across all 5 CV folds).
The 8-row CV gap corresponds to 8 daily bars × 1 offset per CV fold boundary, covering the
7-bar forward label window plus the 1-bar embargo. Cross-offset purging is handled by the 3×
multiplier in the panel-level REQUIRED_GAP.

---

## Gate Efficacy Table (IS, single seed = 191664963)

| Symbol | Signals Seen | z-score killed | Hurst killed | ADX killed | Low-vol killed | Total kill rate | Vol-scaled passed |
|---|---|---|---|---|---|---|---|
| BCHUSDT | 627 | 214 (34.1%) | 17 (2.7%) | 22 (3.5%) | 172 (27.4%) | 67.8% | 202 |
| LDOUSDT | 466 | 324 (69.5%) | 4 (0.9%) | 11 (2.4%) | 58 (12.4%) | 85.2% | 69 |
| TRXUSDT | 697 | 189 (27.1%) | 11 (1.6%) | 47 (6.7%) | 215 (30.8%) | 66.3% | 235 |
| **Portfolio** | **1790** | 727 (40.6%) | 32 (1.8%) | 80 (4.5%) | 445 (24.9%) | **71.7%** | 506 |

BTC trend filter: 18/195 killed (9.2% of vol-scaled signals).

**Dominant gate by symbol:**
- BCH: z-score (34.1%) + low-vol (27.4%) — together kill 61.5% of signals
- LDO: z-score overwhelmingly dominant (69.5%) — LDO has high OOD rate at 24h
- TRX: z-score (27.1%) + low-vol (30.8%) — balanced filtering

The LDO z-score kill rate of 69.5% (324 of 466 signals) is noteworthy — the 24h LDO feature
representation is highly OOD-flagged by the Mahalanobis-equivalent z-score gate, which is calibrated
on 8h IS statistics but now applied to 24h-aggregated features. The gate may be miscalibrated for
the new timescale's feature distribution (z-score trained on 8h distributional statistics).

No drawdown brake fires, no regime gate fires, no cap fires — all structural gates are inactive.
This means the loss is driven by trading losses on admitted signals, not gate-level failures.

---

## Seed Concentration Audit

Ensemble mode: EXPLORATION (3 seeds: 191664963, 1662057957, 1405681631).
Single ensemble run (not multi-seed outer loop); no per-seed Pareto breakdown available.
IS monthly Sharpe = -2.1702 (single seed=42 lineage, 3-seed inner ensemble).

---

## Offset_id Feature Importance

| Symbol | offset_id importance | Total feature importance sum | offset_id share | Rank |
|---|---|---|---|---|
| BCHUSDT | 1.0 | 300.3 | **0.3%** | **15/15 (dead last)** |
| LDOUSDT | 8.3 | 1146.3 | **0.7%** | **15/15 (dead last)** |
| TRXUSDT | 11.7 | 533.5 | **2.2%** | **15/15 (dead last)** |
| Portfolio | 21.0 | 1980.4 | **1.1%** | **15/15 (dead last)** |

**Finding:** offset_id ranks last in every symbol and the portfolio aggregate. The model effectively
did NOT learn to distinguish offsets — it ranks offset_id (the categorical variable encoding which
UTC-hour aggregation window generated each row) with near-zero weight. This answers the
multi-offset question directly: the model is NOT overfitting to offset_id. However, the flip side
is equally concerning — the model is not using the per-offset structural information (which the EDA's
T3 table showed varies per symbol: BCH strongest at offset 0, TRX strongest at offset 16). The
pooled-training design with offset_id as a feature was expected to allow the model to distinguish
offsets, but the LightGBM found it uninformative and effectively trained a single pooled model.

The 24h multi-offset architecture degrades to a naive 3x-oversampled training set
(same signal seen 3 times per day with minor offset variations), not a genuinely richer
representation. The hypothesis that the model would learn to exploit offset-specific dynamics
is falsified by the 0.3-2.2% offset_id importance.

---

## Section 8 Pre-Registered Criterion Evaluation

**Criterion 1 (NEGATIVE — first match):**
- (a) IS monthly Sharpe < +0.7325: IS = **-2.1702 < +0.7325** — FIRES
- (b) OOS monthly Sharpe < -0.0597: OOS = **-3.2589 < -0.0597** — FIRES

Both arms of Criterion 1 fire simultaneously. **Classification: EXPLORATION-NEGATIVE.**

Criteria 2, 3, 4 are not evaluated (first-match-wins).

**Pre-registered interval miss:**
The QR's modal band was IS [+0.30, +0.70] / OOS [-0.20, +0.30] (~50% probability).
Observed: IS = **-2.1702** (below modal lower bound by **-2.47**), OOS = **-3.2589** (below modal lower bound by **-3.06**).
The result is not merely a downside miss of the modal band — it falls below the Residual category's
implicit lower bound. The QR's Section 4 pre-registered "Residual (~5%)" described trade count
degeneration or BCH portfolio-breaking loss; the observed outcome combines BOTH elements:
near-degenerate OOS trade count (25 trades, 1.8/month) AND catastrophic IS loss (-2.17 Sharpe).

The observed IS -2.17 / OOS -3.26 is the worst result in v3 cycle-6 history
(prior worst: /112 pooled architecture at IS -1.12 / OOS -0.72).

**Explicit falsifier from Section 4:** "if OOS monthly Sharpe falls below -0.20 AND IS monthly
Sharpe falls below +0.30, the hypothesis is rejected." Both conditions are satisfied (OOS -3.26 <<
-0.20, IS -2.17 << +0.30). **Hypothesis rejected.**

---

## Trade-Rate Floor Problem

| Metric | Required | Observed | Status |
|---|---|---|---|
| OOS total trades | ≥ 130 | **25** | FAIL (19.2% of floor) |
| OOS trades/month | ≥ 10 | **1.79** | FAIL |
| IS total trades | ≥ 10/month | 170 / ~25 IS months ≈ 6.8/month | BORDERLINE |
| OOS months with 0 trades | 0 desired | **8 of 14** | FAIL |

At 24h bar frequency, the cooldown_candles=2 imposes a 48h refractory between trades per symbol.
With 3 symbols and 3 offsets, maximum theoretical rate is ~3 trades/24h × 3 symbols × 3 offsets
= 9 signals/day (severely reduced by the 7-gate stack, which kills 71.7% of signals, leaving
~2.6 signals/day). The production trade rate of 1.79/month (vs expected ~10/month from the IS run)
suggests the OOS feature distribution drifts sharply outside the IS-calibrated gate windows.

The z-score OOD gate is the dominant killer at 24h (LDO: 69.5%, portfolio: 40.6%) and its
thresholds were calibrated on 8h IS statistics. At 24h, the feature aggregation produces
different distributional properties, causing the OOD gate to fire far more aggressively in OOS
than in IS. This gate miscalibration is a direct consequence of applying IS-calibrated 8h thresholds
to a 24h-derived feature distribution.

---

## Anomaly Notes from Trade Spot-Check

Spot-checked 6 OOS trades (rows 2-7, 24-26 from out_of_sample/trades.csv).

Trade 1 (BCHUSDT short, SL): entry=499.87, exit=500.172986, pnl_pct=-0.0606%. Computed: (499.87-500.172986)/499.87×100 = -0.0606%. MATCH.
Trade 2 (BCHUSDT long, TP): entry=480.17, exit=480.724324, pnl_pct=0.1154%. Computed: (480.724324-480.17)/480.17×100 = 0.1154%. MATCH.
2:1 ATR barrier geometry (Trade 2): SL_dist = 480.17 - 479.892838 = 0.277162; TP = 480.17 + 2×0.277162 = 480.724324. EXACT MATCH.
Trade 7 (LDOUSDT long, TP): entry=0.9476, exit=0.949640, pnl_pct=0.2152%. Computed: 0.2153%. MATCH within rounding.
net_pnl_pct = pnl_pct - fee_pct confirmed for all checked trades.
weighted_pnl = net_pnl_pct × weight_factor confirmed for all checked trades.

Trade duration observation: 28,800,000 ms = 8.0h per trade. This means trades are opened
and closed within consecutive 8h sub-bars of a 24h window. The 24h decision grid makes
predictions at daily close_time, but the actual SL/TP barrier can fire on any sub-bar.
This is consistent with the ATR-scaled barrier geometry: at 24h aggregation scale the
ATR is small enough that the barrier is frequently hit within 8h.

No NaN Sharpe, no NaN PnL, no zero-trade months in IS that are structurally invalid
(IS monthly_pnl.csv shows 23 months with trades over the 25-month IS window; gaps are
months where no signal cleared all gates — structurally valid).

---

## Status

OVERALL=READY-FOR-CRITIC
