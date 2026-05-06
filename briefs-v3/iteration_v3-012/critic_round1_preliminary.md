# Phase 7.5 Critic Review — iter-v3/012 — PRELIMINARY

**Mode**: Round 1 PRELIMINARY (TYPE=EXPLORATION — Checks 1, 2, 4, 5, 6, 8 enforced; Check 3 informational)

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
ZERO src/ code changes. Single behavioral change is `BTC_TREND_CONFIG.threshold_pct` 20.0 → 15.0 (line 121). The BTC trend filter at `risk_v2.py:806-869` is post-hoc — `apply_btc_trend_filter` consumes already-closed trades and operates on `btc_closes[idx - lookback_bars]` where `idx = searchsorted(btc_open_times, trade.open_time, side='right') - 1`. No look-ahead introduced.

### Check 2 — Embargo Width: PASS
CV gap = 88. Labeling parameters UNCHANGED. BTC band tightening operates on a post-hoc filter that doesn't touch CPCV.

### Check 3 — Multiple-Testing Correction: INFORMATIONAL (TYPE=EXPLORATION)
DSR=0.0, PSR=1.0, n_trials=40, n_eff=7, PBO=0.1077 — IDENTICAL to iter-v3/010 and iter-v3/011 (this exact preservation is the null-result fingerprint). PER-CELL TAIL: 13 high-PBO cells with PBO>0.5; 4 with PBO>0.99 (TRX/2025-10=1.00, TRX/2025-11=1.00, MKR/2025-04=0.995, MKR/2025-07=0.991).

### Check 4 — IC Correlation: PASS
Identical to iter-v3/011 (zero new features).

### Check 5 — ADF Stationarity: PASS (inherited)
Feature set unchanged.

### Check 6 — Pareto Dominance: N/A (single-seed EXPLORATION)
1 row in pareto_front.csv per cadence rule.

### Check 8 — Hypothesis-Implementation Alignment: PASS
Single-axis discipline honored. Strict.

### Checks 9, 10: PASS

---

## Anomaly Audit — Engineer's Null-Result Explanation

The engineering report's null-result mechanism is mechanically plausible: BTC kill rate 6.72% → 11.11% (+17 kills); IS/OOS trade counts identical; per-symbol LDO/MKR EXACT match; IS total_pnl drops 97.31% → 73.42% (-23.89pp from zero-weighting 17 additional trades). The Engineer asserts the IS Sharpe drop -0.147 is "a measurement artifact of how BTC filter interacts with weighted-PnL Sharpe calculation" — plausible but unproven analytically.

---

## MKR 5th Consecutive Negative — Pre-Committed Compression Rule TRIGGERED

| Iter | MKR OOS net PnL | MKR OOS WR |
|---|---:|---:|
| iter-v3/007 | -6.5% | 33.3% |
| iter-v3/009 | -13.1% | 30.8% |
| iter-v3/010 | -10.6% | 29.4% |
| iter-v3/011 | -25.75% | 25.0% |
| **iter-v3/012** | **-25.75%** | **25.0%** |

Per `feedback_mkr_threshold_compression.md` (committed in iter-v3/011 cycle, SHA `b9ebbb2`): "If iter-v3/012+ records MKR's 5th consecutive negative, the NEXT EXPLORATION must be a per-symbol-diagnostic axis. Rule cannot be renegotiated post-hoc."

**Rule TRIGGERED.** iter-v3/013 MUST be per-symbol-diagnostic. The ±25% test from brief Section 7 is deferred (MKR rule overrides).

Note: iter-v3/012 MKR is IDENTICAL to iter-v3/011 (-25.75% / 25.0% WR). Sign is negative — counter satisfies "5th consecutive negative" even though magnitude stationary.

---

## Catalog Framing — PROMISING-by-IS-threshold vs NEGATIVE-no-effect

**Argument for EXPLORATION-PROMISING-by-inheritance**:
- IS Sharpe +0.8096 ≥ +0.40 PROMISING threshold
- Falsifier 1 NOT triggered
- Single-axis discipline honored

**Argument for EXPLORATION-NEGATIVE-by-no-effect**:
- Hypothesis "tightening helps" NOT supported (IS dropped -0.147, wrong direction)
- Trade roster IDENTICAL to iter-v3/011 — zero behavioral change
- Cataloguing PROMISING risks downstream CONFIRMATION QR mistakenly bundling ±15% as ingredient when actual finding is "band width in (15%, 20%) is structurally inert"

**Recommendation: EXPLORATION-NEGATIVE-no-effect.** The IS-threshold mechanical pass is misleading; the hypothesis was not supported, and the catalog inheritance must reflect that.

---

## Clarifications Requested from QR

1. **Catalog framing**: Recommend EXPLORATION-NEGATIVE-no-effect (hypothesis "tightening helps" unsupported; band 15-20% structurally inert). Confirm or argue PROMISING with caveats.

2. **MKR rule trigger acknowledgment**: Confirm (a) `feedback_mkr_threshold_compression.md` TRIGGERED, (b) iter-v3/013 brief MUST declare per-symbol-diagnostic axis, (c) any deviation requires new pre-committed rule. Is MKR the only drop candidate, or does TRX (-19.96% IS net PnL) enter the diagnostic conversation?

3. **MKR magnitude stationary**: Trajectory now -6.5% → -13.1% → -10.6% → -25.75% → -25.75% (stationary at iter-v3/011's worst-yet level). Rule says "5th consecutive negative" not "5th consecutive worsening" — confirm satisfied?

4. **±25% looser direction test**: Falsifier 1 NOT triggered → conditional permission doesn't activate. MKR rule overrides anyway. Confirm ±25% deferred to iter-v3/014+ at earliest.

5. **IS Sharpe drop attribution**: Engineer asserts -0.147 drop is weighted-PnL artifact from 17 zero-weight trades. Should diary include quantitative reconciliation (recompute IS Sharpe using iter-v3/011 weight_factors with iter-v3/012 trade roster; should reproduce +0.9566 exactly if mechanism correct)?

6. **Per-cell PBO tail thickening**: 4 cells with PBO>0.99 (vs 5 cells>0.9 in iter-v3/011). 2 new TRX 1.00 cells in newer OOS extent. Flag tail-thickening explicitly in catalog?
