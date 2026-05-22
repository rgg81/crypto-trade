# Engineering Report — iter-v3/116

## Headers

- Iteration: iter-v3/116
- Branch: iteration-v3/116
- Commit SHA (code): d786104ee53aab7805a96bcf071c73b69b139e7b
- Hardware: WSL2 / Intel CPU
- Wall-clock time: 0.70h

---

## Configuration Diff vs /059 Baseline

| Item | /059 canonical | /116 |
|---|---|---|
| `label_mode` | `triple_barrier` | `triple_barrier` (REVERTED from /115 `fixed_horizon`) |
| `DEFAULT_ATR_MULTIPLIERS` | `(2.0, 1.0)` | `(2.0, 1.0)` (unchanged) |
| `V3_ATR_MULTIPLIERS_PER_SYMBOL` | `{}` | `{}` (unchanged) |
| `V3_FEATURE_COLUMNS_TOP_N` | 14 | 14 (unchanged) |
| `V3_MODELS` | `(BCH, LDO, TRX)` | `(BCH, LDO, TRX)` (unchanged) |
| `enable_no_confirm_exit` | (not present) | **True** |
| `no_confirm_trigger_atr` | (not present) | **0.50** |
| `no_confirm_k_candles` | (not present) | **4** |
| `ITERATION_LABEL` | `"v3-059"` | `"v3-116"` |
| ENSEMBLE_SIZE | 10 (CONFIRMATION) | 3 (EXPLORATION) |
| `--n-trials` | 35 | 35 |
| `OOS_CUTOFF_DATE` | 2025-03-24 | 2025-03-24 (IMMUTABLE) |
| `training_months` | 24 | 24 (IMMUTABLE) |

All 16 config-accretion knobs verified PASS at runner pre-flight (run.log line 20).

---

## Key Metrics Block

### Headline

| Metric | In-Sample | Out-of-Sample | Ratio |
|---|---|---|---|
| monthly_sharpe | +0.6246 | +1.1089 | 1.7754 |
| daily_sharpe | 1.4345 | 2.6194 | 1.8260 |
| max_drawdown | 43.87% | 21.88% | 0.499 |
| profit_factor | 1.2438 | 1.4049 | 1.130 |
| win_rate | 29.19% | 42.06% | 1.441 |
| n_trades | 161 | 107 | 0.665 |
| total_pnl | 42.85 | 39.71 | 0.927 |
| monthly_calmar | 0.9767 | 1.8151 | 1.858 |
| weighted_pnl_total | 42.85 | 39.71 | 0.927 |
| dsr | 0.0000 | — | — |
| pbo | 0.1278 | — | — |
| psr | 1.0000 | — | — |
| n_trials | 315 | — | — |
| n_effective_trials | 19 | — | — |

### Anchor Comparison (vs /060 EXPLORATION-mode reference)

| | IS monthly Sharpe | OOS monthly Sharpe |
|---|---|---|
| /060 anchor | +0.8325 | +0.1403 |
| /116 result | +0.6246 | +1.1089 |
| Delta | **−0.2079** | **+0.9686** |

### Per-Symbol (Out-of-Sample, stable `concentration_pct` metric)

| Symbol | OOS n_trades | OOS win_rate | OOS net_pnl_pct | concentration_pct |
|---|---|---|---|---|
| BCHUSDT | 37 | 40.5% | +22.86 | 44.47% |
| LDOUSDT | 13 | 23.1% | −13.08 | −24.85% |
| TRXUSDT | 57 | 52.6% | +46.80 | 80.38% |

Note: `concentration_pct` computed relative to the total positive PnL, used per the iter-v3/114 Critic Recommendation 2. The unstable `pct_of_total_pnl` (near-zero-denominator) is not cited.

### Per-Symbol (In-Sample)

| Symbol | IS n_trades | IS win_rate | IS net_pnl_pct |
|---|---|---|---|
| BCHUSDT | 74 | 40.5% | +59.48 |
| LDOUSDT | 11 | 27.3% | −6.61 |
| TRXUSDT | 76 | 28.9% | −17.52 |

---

## Diagnostic Question 1 — no_confirm Exit-Mechanism Breakdown (CENTRAL QUESTION)

### IS Exit Breakdown (161 total trades)

| exit_reason | count | fraction | mean net_pnl_pct |
|---|---|---|---|
| stop_loss | 92 | 57.1% | −3.14% |
| take_profit | 45 | 28.0% | +6.77% |
| timeout | 10 | 6.2% | +3.16% |
| **no_confirm** | **14** | **8.7%** | **−0.84%** |

IS no_confirm details: 14 trades, mean −0.84%, median −0.65%, min −2.20%, max −0.01%. **All 14 are negative at the no_confirm cut price.** Per-symbol: BCH 6 trades (mean −0.63%), LDO 1 trade (−0.19%), TRX 7 trades (mean −1.12%).

### OOS Exit Breakdown (107 total trades)

| exit_reason | count | fraction | mean net_pnl_pct |
|---|---|---|---|
| stop_loss | 47 | 43.9% | −2.86% |
| take_profit | 46 | 43.0% | +4.29% |
| timeout | 3 | 2.8% | +0.74% |
| **no_confirm** | **9** | **8.4%** | **−0.80%** |
| end_of_data | 2 | 1.9% | −0.54% |

OOS no_confirm details: 9 trades, mean −0.80%, 8 of 9 negative (88.9%). Per-symbol: BCH 3 (mean −0.66%), LDO 1 (−1.93%), TRX 5 (mean −0.65%).

### Mechanism Gate Re-evaluation at Production

**Key finding: the no_confirm rule at production exits trades at candle 4's CLOSE price, which is negative in the vast majority of cases (IS: 14/14; OOS: 8/9).** This appears to contradict the EDA's g2 finding ("cuts winners"). The reconciliation: the EDA's T8 measured HELD-TO-BARRIER PnL (i.e., what the trade would have been if the rule had not fired), while production measures the EARLY-EXIT PnL (the actual candle-4 close). A trade that the rule cuts at −0.84% (candle 4 close) would have gone on to reach its triple-barrier resolution (TP or SL) — and the EDA showed the held-to-barrier mean was +3.26 to +3.75%. So the production no_confirm PnL of −0.84% IS consistent with the EDA: the rule is cutting trades at candle 4's close (a small loss) that would have been modest winners at barrier (mean +3.75% BCH, +2.90% LDO, +3.26% TRX). The rule cuts EARLY at a slight negative, but the counterfactual barrier resolution is positive — so the rule IS reducing total IS PnL, consistent with the EDA's g2 FAIL prediction.

**Spot-check trade geometry — TRX no_confirm (open_time=1760284799999):** LONG at 0.322720, SL=0.317225 (1.703% sl_dist = 1 ATR), TP=0.333711 (2 ATR). Confirm threshold: 0.322720 + 0.50 × 0.005495 = 0.325468. Candle 4 closed at 0.322340 (below entry — did not reach 0.325468). Net PnL: (0.322340 − 0.322720) / 0.322720 × 100 − 0.1% fee = −0.2177%. File: −0.2177%. Geometry verified exact.

---

## Diagnostic Question 2 — Per-Symbol OOS Attribution

### OOS by Symbol: /060 vs /116

| Symbol | /060 n_trades | /060 net_pnl_pct | /116 n_trades | /116 net_pnl_pct | Delta |
|---|---|---|---|---|---|
| BCHUSDT | 37 | −8.69 | 37 | +22.86 | **+31.55** |
| LDOUSDT | 11 | −25.08 | 13 | −13.08 | **+12.00** |
| TRXUSDT | 54 | +30.76 | 57 | +46.80 | **+16.04** |

**Finding: the OOS lift is BROADLY distributed across all 3 symbols.** Every symbol improved materially vs /060. TRX and BCH carry the bulk of the lift; LDO is still negative but meaningfully less so. This is structurally distinct from the /114 frozen-baseline attribution artifact (where improvement was concentrated in the "target" symbol while non-target symbols produced bit-identical results).

### Frozen-Baseline Check

Direct bit-identity comparison of OOS trade rosters (/060 vs /116):

| Symbol | /060 trades | /116 trades | open_time+entry matches | Changed exits | New entries |
|---|---|---|---|---|---|
| BCHUSDT | 37 | 37 | 35/37 (95%) | 3 (no_confirm→TP/SL changed) | 2 new |
| LDOUSDT | 11 | 13 | 11/13 (85%) | 0 changed exits | 2 new |
| TRXUSDT | 54 | 57 | 50/57 (88%) | 6 changed exits | 7 new |

**Verdict: NOT bit-identical.** The trade roster is materially different at all 3 symbols — the no_confirm rule is genuinely changing the book composition, not just reporting an attribution artifact from a frozen model.

---

## Diagnostic Question 3 — Trade Count and Book Composition vs /060

| Period | /060 trades | /116 trades | Delta | New in /116 (not in /060) | Lost from /060 |
|---|---|---|---|---|---|
| IS | 159 | 161 | +2 | 8 new | 6 lost |
| OOS | 102 | 107 | +5 | 11 new | 6 lost |

**OOS new entries in /116 (not in /060): 11 trades, mean net_pnl_pct = +3.67%.** These are trades enabled by the slot-freeing cascade — the no_confirm exit at candle 4 frees the symbol slot earlier than SL/timeout would, allowing the next LightGBM signal to enter sooner.

### Slot-Freeing Cascade Evidence — October 2025 (largest OOS swing: +11.75%)

In October 2025, the /116 no_confirm primitive caused the following cascades:

1. **TRX 2025-10-12 (open_time=1760284799999):** /060 held to stop_loss (−1.80%); /116 exited at no_confirm candle 4 (−0.22%). Slot freed 9 candles earlier. Three new TRX TP entries became possible: +3.49%, +3.62%, +2.96%.

2. **BCH 2025-10-28 (open_time=1761638399999):** /060 held to stop_loss (−3.16%); /116 exited at no_confirm (−0.64%). Slot freed 9 candles earlier. New BCH TP entry enabled: +6.84%.

Net October 2025 effect: /060 = −12.73%, /116 = −0.98% (swing +11.75%). The slot-freeing mechanism is active and directly observable in the monthly trade-by-trade sequence.

**Note on the one reversed case:** TRX open_time=1750262399999 — /060 exited at take_profit (+4.19%), /116 exited at no_confirm (−1.60%). Same model decision (same entry price, direction, barrier geometry). This is a case where the no_confirm rule fired BEFORE the trade confirmed and then reached TP — the rule cut a genuine winner early. This is the EDA's g2 concern manifested in production. The net OOS effect is nonetheless positive because the slot-freeing cascade dominates this individual case.

---

## Seed Concentration Audit

EXPLORATION mode: 3 seeds (191664963, 1662057957, 1405681631), outer=42 lineage subset. Single-seed EXPLORATION per the v3 cadence discipline. No multi-seed concentration audit applicable at EXPLORATION spec; deferred to iter-v3/120 CONFIRMATION.

CPCV: 45 paths, frac_positive_paths = 0.644 (gate threshold 0.55: PASS). Path Sharpe: q25 = −0.243, q50 = +0.335, q75 = +0.838. PBO = 0.1278.

---

## Label Leakage Audit

CV gap = (timeout_candles + 1) × n_symbols = (21 + 1) × 3 = 66 = REQUIRED_GAP. Confirmed at run.log line 36: `Gap: 66 (= (21+1)*3)`. Walk-forward embargo per cell: 22 rows (184h). Verified in CV fold logs (e.g., "train_end=2020-04-24 08:00 | val_start=2020-05-02 00:00 | gap=184h (22 rows)"). No leakage detected. Lookahead bias fix (iter-v3/058 RE-ANCHOR, `e149e9d`) is in effect on this worktree.

---

## Gate Efficacy Table

Risk gate stack: 7-gate RiskV2 stack (vol scaling, ADX-20, Hurst regime, feature z-score OOD zscore_threshold=2.0, low-vol filter, BTC trend alignment at 15%, direction kill-switch disabled). **UNCHANGED from /059 canonical.** No new risk gate introduced in /116. Per-regime table shows only regime="unknown" (regime detection not active), so no per-regime gate breakdown available.

The no_confirm exit primitive interacts with the gate stack at the trade-execution layer (post-entry), not at the gate-decision layer. Gate fire rates are /059-identical (no configuration change to any gate parameter).

---

## Anomaly Notes

1. **IS monthly Sharpe computed by runner (0.6246) vs naive mean/std (1.2985%/7.2019% = 0.180):** The runner uses an annualized or risk-adjusted monthly Sharpe formula, not a raw mean/std ratio. The 0.6246 figure from the runner is the authoritative value; the naive computation from the monthly_pnl.csv is for orientation only.

2. **IS max_drawdown 43.87% vs OOS 21.88%:** IS covers 37 months including the 2022 bear and 2023 chop regimes; OOS covers 14 months in a 2025–2026 uptrend. The asymmetry is structurally expected — not an anomaly.

3. **IS win_rate 29.2% vs OOS 42.1%:** Large OOS win_rate lift. The exit-reason breakdown helps explain: OOS has 43% TPs vs 28% IS — the no_confirm rule's slot-freeing enables entries into subsequent TP-resolving trends in the OOS uptrend regime. The IS 2022–2023 bear/chop regime produces more SL exits (57%) pulling WR down.

4. **TRX open_time=1750262399999 reversed case:** no_confirm cut a genuine winner (held-to-TP in /060 at +4.19%, cut at −1.60% in /116). One of 9 OOS no_confirm exits (11%). Quantitatively small relative to the slot-freeing benefit; noted for Critic inspection.

5. **DSR = 0.0:** Consistent with prior EXPLORATION results at n_trials=315 (n_eff=19). Per `feedback_v3_dsr_mode_artifact.md`, EXPLORATION-mode DSR is a structural artifact and is INFORMATIONAL ONLY. DSR_relative = 1.0 (PASS at threshold 0.95). PSR = 1.0 (PASS at threshold 0.95).

6. **Feature importance: balanced 14-feature stack.** Top features by portfolio importance (last month): ret_skew_200 (9.5%), vwap_dev_20 (8.8%), range_realized_vol_50 (8.2%), ema_spread_atr_20 (8.1%), max_dd_window_50 (7.7%). regime_momentum_signed_5d ranks 14th (5.7%). No single-feature dominance (Herfindahl within normal range).

7. **IC matrix:** Two high-IC pairs: vwap_dev_20 / regime_momentum_signed_5d (IC=0.764) and sym_vs_btc_ret_7d / regime_momentum_signed_5d (IC=0.619), and ema_spread_atr_20 / sym_vs_btc_ret_7d (IC=0.486). These are known algebraic correlations (regime_momentum = ret_5d × sign(hurst−0.5) correlates with momentum features). No unexpected new collinearities introduced by /116.

---

## Section 8 Pre-Registered Classification (first-match-wins)

Anchor: /060 (IS +0.8325, OOS +0.1403).

| Criterion | Threshold | Observed | Fires? |
|---|---|---|---|
| **1a. NEGATIVE: IS < 0.7325** | IS < anchor − 0.10 = 0.7325 | IS = **0.6246** | **YES** |
| 1b. NEGATIVE: OOS < −0.10 | — | OOS = +1.1089 | No |
| 1c. NEGATIVE: OOS/IS < 0 | — | ratio = 1.775 | No |
| 2. SUSPICIOUS: OOS/IS > 3.0 | (not reached — Crit 1 fired first) | ratio = 1.775 | Not evaluated |
| 3. INERT | (not reached) | — | Not evaluated |
| 4. NULL-RESULT | (not reached) | — | Not evaluated |
| 5. PROMISING | (not reached) | — | Not evaluated |

**Classification: EXPLORATION-NEGATIVE (Criterion 1a fires — IS monthly Sharpe 0.6246 < threshold 0.7325).**

This is the modal pre-registered outcome per the brief (Section 7, Mode 1, ~55% likelihood). The IS Sharpe falls 0.21 below the /060 anchor — the early-exit rule imposes a drag on the IS book (the rule cuts trades that would have proceeded to TP in the 2022–2025 IS window's intermittent trends). The OOS result (+1.1089, Δ +0.97 vs anchor) is a large upside miss from the pre-registered 80% band ([−0.10, +0.20]). Section 8 first-match-wins evaluation applies the criterion mechanically without regard to the OOS outperformance — IS Criterion 1a fires first.

**Contextual note for the Critic:** The OOS/IS ratio = 1.78 is WITHIN the healthy [0.5, 2.0] band. The result does NOT fall in the SUSPICIOUS-OOS-DOMINANT taxonomy (Criterion 2, threshold 3.0). The user has explicitly noted that a regime-adaptive exit rule (cut chop-phase trades early; let trend-confirmed trades run) would naturally produce IS Sharpe below the /060 anchor given the 37-month IS window includes the 2022 bear and 2023 chop regimes, while the 14-month OOS window is a 2025–2026 uptrend. This is the correct question for the Critic to adjudicate: is the IS underperformance genuine signal-cost-in-IS-chop-regime or IS-deterioration-without-mechanism?

---

## Evidence-Grounded Preliminary Read

The three diagnostic questions each point in the same direction but with important nuance.

**Diagnostic 1 (mechanism breakdown):** The no_confirm rule fires at 8.7% IS / 8.4% OOS — within the brief's 5–25% sensible regime band. IS no_confirm exits are 100% negative at exit price (all 14 trades closed at a small negative — consistent with "the trade moved adversely in the first 4 candles"). The production g2 question (cuts losers or winners?) resolves to: the rule cuts trades AT CANDLE 4 CLOSE that happen to be at slight negatives — but the EDA's T8 showed these same trades would have been modest winners at barrier (mean +3.26 to +3.75%). So the mechanism is confirmed operating AS DESIGNED (not as the brief hoped): the rule IS reducing total IS PnL by cutting trades early before they reach their TP, consistent with the EDA's g2 FAIL prediction. This supports the NEGATIVE classification mechanically.

**Diagnostic 2 (per-symbol OOS attribution):** ALL three symbols improved OOS vs /060 (BCH +31.55, LDO +12.00, TRX +16.04). This is NOT a frozen-baseline artifact — the trade roster is materially different at all 3 symbols (BCH: 3 changed exits + 2 new entries; TRX: 6 changed exits + 7 new entries; LDO: 2 new entries). The OOS lift is structurally broad, not concentrated in one symbol drift.

**Diagnostic 3 (trade count / slot-freeing cascade):** The slot-freeing cascade is directly observable in October 2025 (the single largest month swing: +11.75%). The no_confirm primitive exits stalled trades 9 candles earlier, enabling new TP entries. The 11 new OOS entries have mean PnL +3.67% — all TPs. The cascade is real and is the primary mechanism of the OOS lift.

**Synthesis:** The evidence splits cleanly. The IS result is NEGATIVE per Section 8 and the mechanism explains why: in the IS 2022–2025 regimes (bear/chop), the early exit cuts trades that would have recovered to TP, imposing a net IS drag. The OOS result is structurally interesting because the 2025–2026 OOS uptrend creates a fertile environment for the slot-freeing cascade: stalled trades that would have been SLs under /060 become no_confirm exits early, freeing slots into the next TP-bound trend. The regime asymmetry between IS and OOS is real and documented.

**What the Critic needs to assess:** whether the IS Sharpe below the negative threshold reflects a genuine signal-cost-in-IS-chop or a structural incompatibility between the early-exit rule and the triple-barrier label estimand (the model trains on triple-barrier labels but the early-exit rule changes the book's PnL profile AFTER training — an architectural coupling issue). If the former, the rule might be a valid regime-adaptive tool that warrants CONFIRMATION-spec testing with a longer OOS or a matched IS-uptrend sub-window. If the latter, the result is a confound with no transferable edge.

The evidence does NOT support reflexive artifact dismissal (OOS/IS ratio 1.78 is healthy; attribution is broad; mechanism is real). It also does not support PROMISING classification (IS Criterion 1a fires unambiguously per the pre-registered gate). The result is EXPLORATION-NEGATIVE on the pre-registered criteria, with a genuine mechanism question worth carrying forward to the Critic's adjudication.

---

## Status

OVERALL=READY-FOR-CRITIC
