# Iteration v2/019 Research Brief

**Type**: EXPLORATION (BTC trend-alignment filter — NEW primitive, addressing IS 2024-11)
**Track**: v2 — risk arm
**Parent baseline**: iter-v2/017 (hit-rate gate, OOS-only scope)
**Date**: 2026-04-14
**Researcher**: QR
**Branch**: `iteration-v2/019` on `quant-research`

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES.
```

## Motivation — the 2024-11 disaster

User feedback after iter-v2/018:
> "IS must be better. Specifically this month 2024-11. The story
> always repeats in the future. And we need to make sure we
> learned from our mistakes."

**Forensic analysis of IS 2024-11** (primary seed, iter-v2/005 data):

- **18 trades, ALL SHORTS (100% direction imbalance)**
- **15 SL hits (83% SL rate)**
- **Net weighted PnL: −73.66%**
- Distribution: DOGE −23.26, NEAR −25.12, SOL −16.53, XRP −8.75

**Market context**: Nov 6, 2024 was the US presidential election.
Trump won. Crypto markets rallied violently. **BTC went from
~$67k to ~$99k in the month (+48%)**. Alts rallied even harder
(DOGE parabolic, SOL/XRP/NEAR all +30-100%).

The model's fault: it was trained on pre-rally October 2024
setups and systematically predicted shorts. The model had no
signal that a regime shift was happening. Every short hit SL.

**Critical property**: BTC's 14-day return during Nov 2024
reached **+30.8%** at peak, and stayed above +20% for most of
the month. **Any short during BTC 14d > +20% is fighting a
post-election regime shift**.

## The "story repeats" insight

The user's framing is crucial:
> "The story always repeats in the future."

Meaning: 2024-11 is not a one-off. Similar regime-shift events
will recur in live trading:
- COVID crash Mar 2020
- LUNA crash May 2022
- FTX crash Nov 2022
- Post-election rally Nov 2024
- Future unknown events

**Any strategy that doesn't detect regime shifts will hit one
of these eventually.** The QR has access to IS data precisely
to identify these patterns and design defenses.

## Diagnostic — BTC trend filter alignment

Testing whether "BTC 14-day return vs trade direction" would
have caught 2024-11:

- Nov 6 (first disaster trade): BTC 14d = **+16.7%** → below ±20%, filter inactive
- Nov 8: BTC 14d = **+21.5%** → CROSSES ±20%, filter would have killed all subsequent shorts
- Nov 10-25: BTC 14d range 25-31% → filter ACTIVE for the entire period

A rule "kill SHORT when BTC 14d > +20%" would have killed
**15 of 18 Nov 2024 trades** (the 3 earliest before BTC reached
+20% would pass through).

## Post-hoc feasibility — the winning configuration

Tested combinations on iter-v2/005 pre-gate stream:

| Config | IS total | OOS total | Nov 2024 |
|---|---|---|---|
| A: Baseline | +25.82 | +94.01 | −73.66 |
| B: Hit-rate only (iter-017) | +25.82 | +119.94 | −73.66 |
| C: Hit-rate IS+OOS | −91.82 | +119.94 | −60.31 |
| D: **BTC 14d ±20 filter only** | **+116.72** | **+99.90** | **−28.68** |
| **E: BTC 14d ±20 + hit-rate OOS-only** | **+116.72** | **+125.82** | **−28.68** |
| F: BTC + hit-rate IS+OOS | −43.29 | +125.82 | −28.68 |

**Config E wins**: IS jumps from +25.82 to +116.72 (**+352%**),
OOS from +94.01 to +125.82 (**+34%**, better than iter-017 alone),
Nov 2024 from −73.66 to −28.68 (**−61% loss**).

## Hypothesis

Adding a BTC 14-day trend filter BEFORE the hit-rate gate:

1. **Catches IS regime-shift disasters** (2024-11, 2023-10, 2022-05)
2. **Does NOT hurt OOS** (in fact helps OOS by ~+6 vs iter-017)
3. **Targets a specific, well-defined market event** (BTC 14d > ±20%)
4. **Requires no retraining** — post-hoc filter on trade outputs
5. **Complementary to the hit-rate gate** — the two gates catch
   different failure modes

## Pre-registered failure-mode prediction

**Primary failure mode**: the 2025 OOS period has no BTC ±20%
move during v2's worst drawdown (July-August 2025). So the
filter doesn't fire in that window, and the hit-rate gate is
still the primary OOS defense. This is the expected separation
of concerns:
- BTC filter: IS regime shifts (2022, 2024-11)
- Hit-rate gate: OOS slow bleeds (July 2025)

**Secondary failure mode**: in some seeds, BTC filter might kill
legitimate contrarian winners during mild BTC uptrends. But
the ±20% threshold is strict enough to avoid this on iter-005
primary seed data.

**Tertiary failure mode**: seed variance on the filter's effect.
Most seeds share the same trade direction decisions (they
differ mainly on confidence thresholds), so the BTC filter's
kill list should be similar across seeds. Expected: all 10
seeds see IS improvement.

## Configuration

**Code changes**:

1. `src/crypto_trade/strategies/ml/risk_v2.py`:
   - Add `BtcTrendFilterConfig` dataclass
   - Add `BtcTrendFilterStats` dataclass
   - Add `apply_btc_trend_filter(trades, btc_closes, btc_times, config)`
     function
2. `run_baseline_v2.py`:
   - Bump `ITERATION_LABEL` to `"v2-019"`
   - Load BTC 8h klines at startup
   - Apply BTC filter FIRST, then hit-rate gate (on the
     post-BTC stream)
   - Apply BTC filter with `activate_at_ms=None` (full period)
   - Apply hit-rate gate with `activate_at_ms=OOS_CUTOFF_MS`
     (OOS only, unchanged)
   - Record both filter stats in `seed_summary.json`

**Thresholds** (Config E from feasibility):

| Param | Value |
|---|---|
| BTC lookback bars | 42 (14 days of 8h bars) |
| BTC threshold pct | 20.0 |
| Hit-rate gate | unchanged (window=20, SL_threshold=0.65) |

## Validation

**Phase 1 — 1-seed fail-fast** (seed 42, ~5 min):
- Must produce the same IS/OOS totals as Config E feasibility
  (+116.72% IS, +125.82% OOS)
- 2024-11 braked total must be around −28.68%
- At least 30 trades killed by BTC filter (feasibility: 39 BTC kills)

**Phase 2 — 10-seed validation** (if phase 1 passes):
- 10-seed mean OOS Sharpe ≥ +1.5 (target, stricter than iter-017's +1.1 fallback)
- ≥ 9/10 seeds profitable
- All seeds IS MaxDD improved vs baseline
- Primary seed concentration ≤ 50%

## Success Criteria (MERGE decision)

All must pass:
- [ ] Phase 1 1-seed matches feasibility
- [ ] 10-seed mean OOS Sharpe ≥ +1.5
- [ ] ≥ 9/10 profitable
- [ ] Primary seed IS total PnL > iter-v2/005's +25.82 (strict IS improvement)
- [ ] **Primary seed 2024-11 total PnL > −40 weighted** (directly addresses user's ask)
- [ ] Primary seed concentration ≤ 50%
- [ ] IS/OOS ratio preserved or improved

## Section 6: Risk Management Design

### 6.1 Active gates (iter-v2/019)

1. Feature z-score OOD (|z| > 3)
2. Hurst regime check (5/95 IS percentile)
3. ADX gate (threshold 20)
4. Low-vol filter (atr_pct_rank_200 < 0.33)
5. Vol-adjusted sizing (scale = atr_pct_rank_200, clipped 0.3-1.0)
6. **NEW: BTC trend filter (14d ±20%, full period)**
7. Hit-rate feedback gate (window=20, SL threshold=0.65, OOS-only)

### 6.2 BTC trend filter mechanics

Rule: at each trade's open_time, compute BTC 14-day (42-bar)
return. If the trade's direction fights a BTC trend of >20% in
the opposing direction, kill the trade.

```python
def btc_filter_fires(direction, btc_14d_ret):
    if direction == -1 and btc_14d_ret > +20.0:
        return True  # short vs strong uptrend
    if direction == +1 and btc_14d_ret < -20.0:
        return True  # long vs strong downtrend
    return False
```

Key properties:
- **Symmetric**: long and short treated the same way
- **Cross-asset**: uses BTC as the trend signal for all 4 alts
- **No state**: purely local to each trade (no rolling state)
- **Rare firing**: ±20% 14-day BTC moves happen maybe 5-10 times
  per year in extreme regimes

### 6.3 Pre-registered failure-mode prediction

See §"Pre-registered failure-mode prediction" above.

### 6.4 Expected firing rates

From feasibility on iter-v2/005 primary seed stream (461 trades
across IS+OOS):
- ~39 kills expected (~8% of total)
- 15 kills in Nov 2024 specifically
- 6-10 kills in 2022 bear market (LUNA, FTX)
- 0-5 kills in 2024-03 rally
- Few kills in 2025 OOS period (BTC was relatively calm)

### 6.5 Black-swan replay — BTC as the crisis signal

Historical BTC ±20% 14-day events this filter would catch:
- 2020-03-12: COVID −50% in 1 day → 14d return instantly < −20%
- 2021-05-12: −40% crash → −20%
- 2022-01, 2022-05 (LUNA), 2022-06, 2022-11 (FTX) — multiple bear crashes
- 2024-03 rally phase → +20% (would kill longs too aggressive)
- 2024-11 post-election rally → +30% (THE target event)
- 2026-01 (if any crash in 2026 OOS)

The filter is designed to be rare and only activate on extreme
regime events. False-positive cost is low because contrarian
bets during ±20% 14d BTC moves are usually wrong.

## Research Checklist (7+ consecutive merges since iter-v2/017)

Actually, iter-v2/017 broke a NO-MERGE streak, so we're on
"1 merge" now. Full research checklist applies because this is
a new primitive addressing user-specific feedback.

- **A-H**: unchanged from iter-v2/017 baseline
- **I (risk management)**: NEW primitive targets IS regime-shift
  disasters, specifically the 2024-11 post-election rally
  pattern. Directly responds to user feedback. Pre-registered
  complementarity with hit-rate gate (different failure modes).
