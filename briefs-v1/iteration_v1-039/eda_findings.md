# iter-v1/039 — EDA Findings: Per-Symbol Drawdown BINARY KILL Brake

**Run date**: 2026-05-31
**Data source**: `reports-v1/iteration_v1-baseline/in_sample/trades.csv` (621 IS trades, 2022-01-01 to 2025-03-23, 39.4 months).
**Script**: `analysis/iteration_v1-039/eda.py`
**CSV outputs**: `analysis/iteration_v1-039/{dd_percentiles,trade_buckets,skip_impact,oscillation,deadlock_risk}.csv`

## Mechanism under study

Per-symbol cumulative net-PnL series at 8h cadence (synthesized from realized
weighted PnL on trade close_time). Rolling-30d (90-bar trailing) peak-to-current
realized drawdown. **Brake ON** when `dd > threshold_sym`; **brake OFF** when
`dd < threshold_sym × 0.5`. While ON, skip ALL new entries on that symbol.

Distinct from /038 (vol CEILING, scale-down). This is **binary KILL on DD**.

---

## 1. Per-symbol DD percentile table (rolling-30d, peak-to-current)

| Symbol | p50 | p75 | p85 | p90 | p95 | p99 | max | n_bars |
|---|---|---|---|---|---|---|---|---|
| BTCUSDT  | 1.75% | **3.88%** | 4.99%  | 5.78%  | 7.93%  | 12.91% | 16.77% | 3547 |
| ETHUSDT  | 1.61% | **4.31%** | 6.02%  | 7.64%  | 9.78%  | 18.83% | 20.78% | 3547 |
| LINKUSDT | 2.65% | **6.44%** | 8.59%  | 9.54%  | 12.88% | 17.91% | 22.84% | 3547 |
| LTCUSDT  | 2.23% | **6.60%** | 9.07%  | 10.83% | 15.54% | 18.98% | 18.98% | 3547 |
| DOTUSDT  | 0.43% | **2.77%** | 4.15%  | 6.86%  | 10.44% | 12.69% | 15.45% | 3547 |

Heterogeneity is significant — LINK/LTC have nearly 2× the p75 DD of DOT/BTC.
Per-symbol thresholds are MANDATORY; portfolio-uniform would over-skip DOT/BTC
and under-skip LINK/LTC.

## 2. Recommended thresholds

`threshold_sym = p75(rolling_30d_dd_sym)`, `recovery = threshold × 0.5`:

| Symbol   | threshold | recovery |
|---|---|---|
| BTCUSDT  | 3.880% | 1.940% |
| ETHUSDT  | 4.307% | 2.153% |
| LINKUSDT | 6.441% | 3.221% |
| LTCUSDT  | 6.601% | 3.300% |
| DOTUSDT  | 2.770% | 1.385% |

## 3. Skip-rate prediction (IS, ORACLE — same realized roster)

| Symbol   | total | skipped | skip rate | retained sum w-PnL | skipped sum w-PnL | retained mean | skipped mean |
|---|---|---|---|---|---|---|---|
| BTCUSDT  | 113 | 36 | **31.9%** |  -30.56% |  +15.54% |  -0.397% | **+0.432%** |
| ETHUSDT  | 145 | 48 | **33.1%** |  -13.90% |   -2.07% |  -0.143% |  -0.043% |
| LINKUSDT | 146 | 37 | **25.3%** |  +20.23% |  +76.17% |  +0.186% | **+2.059%** |
| LTCUSDT  | 124 | 31 | **25.0%** |  +18.82% |  -13.98% |  +0.202% |  -0.451% |
| DOTUSDT  |  93 | 33 | **35.5%** |   -4.60% |  -11.59% |  -0.077% |  -0.351% |

**Aggregate**: 185/621 = **29.8%** IS trades killed. ~5/15 per OOS month → OOS
trade count would drop ~189 → ~133 (still above the ≥130 floor, but barely;
the OOS/month rate falls below the 10/month floor for some symbols).

## 4. Mechanism load-bearing test — DOES IT FIRE THE RIGHT WAY?

**This is the killer finding.** The mechanism is supposed to skip
MORE-NEGATIVE trades. Let's see the sign per symbol:

| Symbol   | retained mean w-PnL | skipped mean w-PnL | mechanism direction |
|---|---|---|---|
| BTCUSDT  | -0.397% | **+0.432%** | **BACKWARD** (skips PROFITABLE trades) |
| ETHUSDT  | -0.143% | -0.043%     | **BACKWARD** (skips LESS-NEGATIVE) |
| LINKUSDT | +0.186% | **+2.059%** | **BACKWARD-CATASTROPHIC** (skips MOST PROFITABLE — LINK is the IS top contributor) |
| LTCUSDT  | +0.202% | -0.451%     | **FORWARD** (skips losses — only 1/5) |
| DOTUSDT  | -0.077% | -0.351%     | **FORWARD** (skips losses) |

**4 of 5 symbols show BACKWARD or only-marginally-forward.** On LINK,
the brake kills the *single richest signal in the entire IS roster*
(`+76.17%` from 37 trades, mean **+2.059%/trade**) — these are the trades
where price has corrected ~6%+ and the model leans long into a bounce.
On BTC, the same pattern: post-drawdown is when the model is *right*.

Only LTC and DOT show the "expected" direction, and DOT's gain is tiny
(-0.077% → -0.351% is small absolute).

**Net IS PnL impact** (sum skipped, sign-flipped because the mechanism
removes those trades from the realized PnL):
- BTC: removing skipped trades removes +15.54% of PnL → **WORSE**
- ETH: removes -2.07% → +2.07% PnL improvement (tiny)
- LINK: removes +76.17% → **catastrophic IS PnL loss**
- LTC: removes -13.98% → +13.98% improvement (good)
- DOT: removes -11.59% → +11.59% improvement (good)

**Aggregate Δ-IS-PnL ≈ -76.17 - 15.54 + 2.07 + 13.98 + 11.59 ≈ -64.07%
PnL on the IS sum.** Baseline IS PnL = +50.98%. Implementing this brake
would push IS PnL strongly NEGATIVE.

**Decile evidence** (trade_buckets.csv): on LINK, D10 (highest DD-at-entry)
is `mean=+4.69%/trade, sum=+70.29%` — the brake would kill the single most
profitable decile in the dataset. Similar pattern on BTC D7-D9.

**Interpretation**: drawdown in v1's per-symbol PnL curve is a PROXY FOR
RECENT LOSING TRADES, and the model's edge is to FADE those losing trades
on the next signal (i.e. mean-reversion in model's own PnL). The brake
mistakes the high-DD region as "regime hostile" when it's actually
"setup for the next winner".

## 5. Oscillation stability

| Symbol   | transitions | on_bars | on_share | transitions/year |
|---|---|---|---|---|
| BTCUSDT  | 26 | 1104/3547 | 31.1% | 8.0 |
| ETHUSDT  | 27 | 1036/3547 | 29.2% | 8.3 |
| LINKUSDT | 30 | 1017/3547 | 28.7% | 9.3 |
| LTCUSDT  | 26 | 1046/3547 | 29.5% | 8.0 |
| DOTUSDT  | 18 | 1039/3547 | 29.3% | 5.6 |

Recovery-factor 0.5 gives 5–9 transitions/year per symbol — well damped.
Hysteresis is fine. Brake is "ON" ~29% of bars in ORACLE.

## 6. STATEFUL deadlock risk assessment

**(a) Can the brake enter a no-trade equilibrium?**
**YES, in principle.** In closed-loop:
- Brake turns ON because rolling-30d DD > threshold.
- While ON, no NEW entries. Open trades still close (exits fire on bar SL/TP/timeout).
- Once all open trades close, cum_pnl is FROZEN (no new contributions).
- `dd = peak − cum_pnl` is then CONSTANT for as long as no trade closes.
- If `dd > threshold × 0.5` at that frozen moment → recovery condition
  never fires → **deadlock**.

**(b) Does the recovery rule (dd < threshold × 0.5) prevent it?**
**NO**, by itself. Recovery requires cum_pnl to RISE, which requires a
WIN, which requires a trade, which the brake forbids.

**(c) ORACLE evidence on deadlock likelihood**:
Longest ORACLE brake-ON run per symbol:
- BTC 293 bars (**97.7 days**)
- LINK 203 bars (67.7 days)
- DOT  208 bars (69.3 days)
- LTC  152 bars (50.7 days)
- ETH  148 bars (49.3 days)

In ORACLE these recovered because the realized roster includes wins. In
**closed-loop, these wins would NOT FIRE** (the brake is ON). So the
closed-loop max-on run is unbounded by the ORACLE upper bound — could be
the full 39 months of IS.

**(d) Proposed deadlock mitigations** (for brief Section 2):
1. **TIME-DECAY recovery**: also turn OFF after `max_on_bars` (e.g. 30 bars / 10 days). Bound the brake to be at most 10 days even if DD doesn't recover. Trades off mechanism integrity for liveness.
2. **PROBE TRADE**: every N bars while ON, allow ONE entry through. PnL contribution from probe trades unfreezes cum_pnl.
3. **DD-on-equity-curve-OF-SIGNALS** (not on realized PnL): use the model's predicted-PnL trajectory (forecast aggregation) instead of realized PnL. Stays alive even with no trades. Best mathematical fix but doubles implementation complexity.
4. **Closed-loop simulator**: build an event-driven simulator that replays the IS bar stream, feeds the brake state into entry decisions, and measures real (not ORACLE) skip behavior. **Mandatory before any CONFIRMATION.**

Per `feedback_v3_oracle_eda_validity.md` (codified iter-v3/054):
**ORACLE EDA is INVALID for stateful primitives. This iteration MUST
include a closed-loop simulation plan in brief Section 2.**

## 7. Brief recommendation (Phase 5 verdict)

**Mechanism is BACKWARD on 3 of 5 symbols, including the largest IS PnL
contributor (LINK at +76% skipped-trade-sum).** The hypothesis that
"high-DD regime → skip entries" does not hold for v1's per-symbol PnL
curves under the model's directional signal. Confirming this in
EXPLORATION is still defensible (single-axis, low cost, novel
mechanism), but the EDA prior strongly suggests **NEGATIVE** verdict.

**Path forward options for the brief**:
1. **Run as-is** with the per-symbol p75 thresholds and document the
   prior expectation of NEGATIVE based on this EDA. ORACLE/closed-loop
   gap could surprise.
2. **INVERT the mechanism** (skip on LOW DD, enable on HIGH DD) — but
   this is no longer a "drawdown brake", it's a "drawdown opportunity
   gate", and it should be a separate iteration with its own brief.
3. **Switch axis** to a different risk primitive (regime gate, cross-symbol
   correlation per the menu's /042). Cycle-5 menu has /042 unused.
4. **Use signal-equity-curve drawdown** instead of realized PnL — turns
   into a model-confidence axis, structurally different.

**My recommendation**: proceed with option 1 (RUN AS-IS) under a HIGH-RISK
declaration with the deadlock mitigation #1 (time-decay OFF after 30 bars
= 10 days; well below the longest ORACLE on-window so it materially
changes behavior in closed-loop). This is the cleanest single-axis
EXPLORATION of the binary-KILL-on-DD primitive, and the EDA's strong
NEGATIVE prior is exactly the kind of "uncertainty I want to resolve"
the Prime Directive demands.

Brief Section 2 must include the deadlock-impossibility argument under
the time-decay rule and a closed-loop simulation outline.
