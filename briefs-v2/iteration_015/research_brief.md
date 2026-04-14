# Iteration v2/015 Research Brief

**Type**: EXPLORATION (BTC contagion circuit breaker feasibility)
**Track**: v2 — risk arm
**Parent baseline**: iter-v2/005 (10-seed mean +1.297)
**Date**: 2026-04-14
**Researcher**: QR
**Branch**: `iteration-v2/015` on `quant-research`

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES.
```

## Motivation — the only risk primitive left that bypasses XRP dominance

iter-v2/012, 013, 014 closed the drawdown brake lineage. Both the
portfolio brake (iter-v2/013) and the per-symbol brake
(iter-v2/014) failed the concentration rule because XRP's
dominance is structural: any brake that attenuates non-XRP symbols
relative to XRP amplifies XRP's share.

iter-v2/014's diary identifies ONE remaining risk primitive that
could work: the **BTC contagion circuit breaker** (Primitive #6
from iter-v2/001's skill). Its key property is **symmetric
cross-asset attenuation** — when triggered, it kills ALL v2
positions simultaneously regardless of per-symbol state. This
preserves the per-symbol ratio because all symbols experience the
same attenuation window.

The contagion brake is also **complementary** to the existing
gates: z-score OOD detects per-symbol feature distributional
drift, Hurst detects per-symbol regime shifts, ADX detects ranging
regimes, low-vol filter detects low-vol regimes. None of them see
a single cross-asset event like "BTC just crashed 8%", which is
the primary correlated-crash vector in crypto markets.

## Hypothesis

A BTC contagion trigger based on **BTC 8h bar return < threshold**
(plus an optional 3-bar 24h return threshold) with a **kill
window** of N bars following the trigger will:

1. **Not materially change Sharpe** because BTC crashes happened
   rarely during 2025-03 to 2026-03 (the OOS window). Cumulative
   brake firing count is expected to be small (~5-15 trades).
2. **Preserve concentration** because the kill is symmetric
   across all 4 symbols. XRP's share stays near 47.75%.
3. **Reduce MaxDD** ONLY if the large drawdowns were
   BTC-correlated. If they were alts-specific (NEAR/XRP-only),
   the brake misses them and MaxDD is unchanged.
4. **Best case**: the July-August 2025 bear stretch was
   BTC-correlated; brake fires, reduces MaxDD, preserves
   concentration. Triple win.
5. **Worst case**: July-August 2025 was alts-specific; brake
   never fires; result is identical to baseline iter-v2/005.

## Pre-registered failure-mode prediction

Most likely failure mode: **BTC didn't materially crash during
2025 OOS**, so the contagion brake doesn't fire at all. Looking at
the macro backdrop, 2025 was a bull year for crypto with BTC
reaching new highs. The July-August 2025 v2 drawdown may have
been alt-specific rather than BTC-correlated.

**Alternative failure mode**: BTC crashed during periods where v2
was not trading, so the brake fires but has no effect on trades.

**Secondary failure mode**: the threshold is too tight
(e.g., −3% 8h bar) and fires on routine volatility, killing
profitable trades.

**Best case**: BTC had 2-5 significant crashes during 2025 OOS,
each within a day or two of v2's worst days. Brake fires on
those, catching real tail events.

**Decision criterion**:
- **Success**: at least one config reduces MaxDD by ≥15% while
  preserving Sharpe within ±5% AND concentration stays within
  5 pp of baseline 47.75%.
- **Failure**: all configs either have no effect OR fail one of
  the preservation rules.

## Methodology — post-hoc simulation

### Data sources

- **v2 OOS trades**:
  `reports-v2/iteration_v2-005/out_of_sample/trades.csv`
- **BTC 8h klines**: `data/BTCUSDT/8h.csv` (existing data from the
  v1 pipeline, used for regime annotation in reports; not a v2
  feature input, just a signal source for the brake)

Using BTC as a signal source is ALLOWED because this is a
cross-asset **trigger** (not a training feature). The no-v1-
features rule applies to model inputs, not risk gates. The skill's
"Relationship to v1" section explicitly allows cross-asset
signals in risk gates (Primitive #6 is literally named "BTC
contagion circuit breaker").

### Algorithm

1. Load BTC 8h klines for the OOS period.
2. Compute:
   - `ret_1bar`: `(close - open) / open` for each bar
   - `ret_3bar`: rolling 3-bar cumulative return (24h rolling)
3. Flag contagion events:
   - `ret_1bar < threshold_1bar` (e.g., −4%)
   - OR `ret_3bar < threshold_3bar` (e.g., −10%)
4. Build a kill-window mask: for each flagged bar, mark the next
   `kill_bars` bars (including the flagged bar) as "kill".
5. For each v2 trade, check if its `open_time` falls in a kill
   window. If yes, zero out `weighted_pnl` (the trade doesn't
   happen).
6. Recompute aggregate and per-symbol metrics on the filtered
   trade stream.

### Configurations to test

| Config | 1-bar thresh | 3-bar thresh | Kill bars (8h each) | Description |
|---|---|---|---|---|
| A | −3% | −8% | 3 (1 day) | Tight: routine vol too |
| **B** | **−4%** | **−10%** | **3** | **Mid: sharper drops** |
| C | −5% | −12% | 6 (2 days) | Loose: tail only, longer kill |
| D | −4% | −10% | 9 (3 days) | Mid threshold, extended kill |
| None | ∞ | ∞ | 0 | Baseline |

## Configuration

**New script**: `analyze_btc_contagion.py`. Reads iter-v2/005 OOS
trades and BTC 8h klines, runs 4 brake configurations post-hoc,
reports aggregate + per-symbol + concentration metrics.

## Success Criteria

Feasibility passes if ANY config:
- [ ] Reduces MaxDD by ≥ 15% vs iter-v2/005 baseline (59.88% → ≤ 51%)
- [ ] Sharpe drag ≤ 5% (trade-level ≥ +1.58 after brake)
- [ ] Concentration change ≤ 5 pp (XRP ≤ 52.75%)
- [ ] No per-symbol negative flip

If feasibility passes, iter-v2/016 productionizes via the runner's
post-hoc trade filter.

## Section 6: Risk Management Design

### 6.1 Active gates (unchanged from iter-v2/005)

- Feature z-score OOD (|z| > 3)
- Hurst regime check (5th/95th IS percentile)
- ADX gate (threshold 20)
- Low-vol filter (atr_pct_rank_200 < 0.33)
- Vol-adjusted sizing (scale = atr_pct_rank_200, clipped 0.3-1.0)

### 6.2 New gate — BTC contagion circuit breaker (POST-HOC SIMULATION)

- Signal source: BTC 8h klines, 1-bar and 3-bar rolling returns
- Trigger: either metric crosses the threshold
- Action: SYMMETRIC attenuation — all v2 signals killed during
  the kill window
- Scoping: active from OOS_CUTOFF_MS onwards (brake "live" at
  OOS deployment boundary)

### 6.3 Pre-registered failure-mode prediction

See §"Pre-registered failure-mode prediction" above. Summary:
most likely is "brake never fires" because 2025 was a bull BTC
year. Backup failure mode: "brake fires but July-August 2025 was
alts-specific, so aggregate metrics are unchanged".

### 6.4 Expected gate firing rates

| Config | Expected trigger events | Expected trades killed |
|---|---|---|
| A (−3%/−8%) | 5-15 | 5-20 |
| B (−4%/−10%) | 3-8 | 3-12 |
| C (−5%/−12%) | 1-3 | 2-6 |
| D (−4%/−10%, kill=9 bars) | 3-8 | 8-25 |

### 6.5 Black-swan replay

The biggest recent BTC crashes:
- 2020-03-12: COVID dump, BTC −50% in 24h (pre-OOS)
- 2022-05-12: LUNA dump, BTC −15% in 24h (pre-OOS)
- 2022-11-08: FTX dump, BTC −17% in 24h (pre-OOS)

None of these are in the 2025-03-24 → 2026-03-xx OOS window.
**Within the OOS window**, the question is whether 2025 had any
BTC event deep enough to trigger the brake. We'll find out from
the data.

## Research Checklist Coverage (7+ consecutive NO-MERGE rule)

### Category A — strategy family: unchanged (LightGBM)
### Category B — feature set: unchanged (35 v2 features)
### Category C — labeling: unchanged (ATR 2.9/1.45)
### Category D — risk layer: NEW primitive (BTC contagion)
### Category E — hyperparameters: unchanged
### Category F — training window: unchanged (24mo)
### Category G — symbol selection: unchanged
### Category H — seeding: no retraining this iteration
### Category I — risk management analysis:
  BTC contagion is the 6th deferred primitive. Symmetric attenuation
  architecture specifically chosen to avoid the XRP dominance
  failure mode from iter-v2/013-014.
