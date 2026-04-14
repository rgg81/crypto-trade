# Iteration v2/013 Diary

**Date**: 2026-04-14
**Type**: EXPLOITATION (productionize drawdown brake)
**Track**: v2 — risk arm
**Branch**: `iteration-v2/013` on `quant-research`
**Parent baseline**: iter-v2/005 (10-seed mean +1.297, XRP 47.75%)
**Decision**: **NO-MERGE** (concentration strict fail 78.55% vs 50% rule)

## What happened

iter-v2/012 ran a post-hoc feasibility study of the drawdown brake
and showed Config C (8%/16%) reduces seed-42 OOS MaxDD from −45% to
−13% while only costing −5% Sharpe. Feasibility PASSED all decision
criteria. iter-v2/013 was the productionization: move that same
post-hoc math into `run_baseline_v2.py` and run the full 10-seed
MERGE validation.

The brake worked **as a risk primitive**: 10-seed mean Sharpe +1.146
(above +1.1 threshold), 9/10 profitable, primary seed MaxDD 16.41%
(73% improvement vs baseline 59.88%). These are good results.

**But the brake broke the portfolio in a way the feasibility study
didn't reveal**: per-symbol concentration rebalanced from a
diversified 4-symbol portfolio to a near-pure XRP exposure.

## The headline numbers

### Aggregate (looked fine)

| Metric | iter-v2/005 | iter-v2/013 | Δ |
|---|---|---|---|
| 10-seed mean Sharpe | +1.297 | +1.146 | −11.7% (drag) |
| Profitable seeds | 10/10 | 9/10 | −1 |
| Primary seed 42 Sharpe | +1.671 | +1.596 | −4.5% |
| Primary seed 42 MaxDD | −59.88% | **−16.41%** | **−73%** |
| Primary seed 42 PF | 1.457 | 1.567 | +7.5% |

### Per-symbol (broken)

| Symbol | iter-v2/005 wpnl | iter-v2/013 wpnl | Share iter-v2/005 | Share iter-v2/013 |
|---|---|---|---|---|
| XRPUSDT | +44.89 | +46.84 | 47.75% | **78.55%** |
| DOGEUSDT | +11.52 | +26.06 | 12.25% | +43.70% |
| SOLUSDT | +28.89 | **−0.18** | 30.74% | **−0.31%** |
| NEARUSDT | +8.71 | **−13.08** | 9.26% | **−21.94%** |

SOL and NEAR flipped from positive to NEGATIVE contributors. XRP's
weighted share blew out from 47.75% to **78.55%**, violating the
≤50% strict rule by 28.55 percentage points.

## Root cause — trade-by-trade forensics

Compared iter-v2/005 and iter-v2/013 DOGE OOS trades one by one (31
trades, same open_time, same net_pnl_pct — confirmed it's the same
underlying backtest with just the brake applied post-hoc).

**The July-August 2025 drawdown window** (trades 9-19 in DOGE's OOS
sequence):

- The brake enters FLATTEN state around 2025-07-17 (shadow equity
  DD ≥ 16%) and stays flattened until 2025-08-20 (shadow equity
  recovers above −8%).
- **11 DOGE trades** fall in this window. In iter-v2/005 baseline
  they sum to **−21.50 weighted_pnl** (8 losses, 3 wins). The brake
  zeros all of them → DOGE gets +21.50 back.
- **During the SAME flatten window**, SOL and NEAR had mostly
  WINNERS (they're momentum plays that were late to the bear
  signal). The brake zeros their winners too → SOL and NEAR lose
  their positive contributions.

**Net effect**:
- DOGE: +14.54 improvement (brake saved losses)
- SOL: −29.07 regression (brake killed winners)
- NEAR: −21.79 regression (brake killed winners)
- XRP: ~unchanged (its July-August trades had mixed outcomes,
  brake's net effect was small)

The blanket flatten rule cannot distinguish which symbols are
currently winning vs losing. It zeros everything during a portfolio
DD, no matter who's contributing to that DD.

## Lessons Learned

### 1. Feasibility studies validate aggregate metrics, not portfolio decomposition

iter-v2/012's Config C delivered +5.31 Calmar, −71% MaxDD, −5%
Sharpe drag. All aggregate metrics looked great. But iter-v2/012
didn't decompose the effect PER SYMBOL. Had it done so, the
cross-symbol contamination would have been visible in the
feasibility numbers too.

**Generalization**: whenever a risk primitive operates on the
POOLED trade stream (not per-model), the feasibility analysis
must include per-symbol decomposition. Check whether any symbol
goes from positive to negative, or whether concentration jumps
by more than 5 percentage points.

### 2. Portfolio-level attenuators have an asymmetry problem

A portfolio-level brake that fires on aggregate DD cannot see
which symbols are currently net-positive contributors within the
drawdown window. It flattens the winners along with the losers,
which:
- Improves aggregate Sharpe slightly (because losers outnumber
  winners in expectation during a DD)
- Kills some symbols' legitimate PnL contributions
- Rebalances per-symbol exposure in unpredictable ways

**Implication**: any trade-level attenuation primitive (not just
drawdown brakes, but also volume-spike shrinks, volatility-clamp
sizers, etc.) needs **per-symbol state** to avoid this asymmetry.

### 3. Concentration rules should use weighted_pnl, not net_pnl_pct

Looking at iter-v2/005's `per_symbol.csv`, it reports XRP at
**50.42%** on the `pct_of_total_pnl` column. But iter-v2/005
merged with "concentration PASS 47.75%" in its diary. The
discrepancy is because `per_symbol.csv` uses unweighted
`net_pnl_pct` while iter-v2/011's combined analysis (and the
brake's concentration check) use `weighted_pnl`.

The weighted metric is the right one for capital allocation,
because it reflects the actual dollar contribution of each
symbol. The unweighted metric is misleading — a symbol with
small weight_factor scaling contributes much less than its
raw net_pnl_pct suggests.

**Action item**: iter-v2/014+ should standardize on
`weighted_pnl`-based concentration. The `iteration_report.py`
module should probably emit both columns.

### 4. The "Sharpe drag is predicted, concentration is the real blocker"

The research brief predicted a ~−0.2 Sharpe drag from the brake and
got −0.15. The Sharpe prediction was nearly perfect. What the brief
missed was the concentration side effect, which I didn't even
think about when writing the brief.

**Generalization**: failure-mode prediction needs to cover
constraints that aren't part of the primary metric. The v2
success criteria include concentration, MaxDD, IS/OOS ratio, etc.
Each of these should get a one-sentence pre-registered prediction.

### 5. The brake helped DOGE, hurt NEAR — what it means

The brake saved DOGE from a −21.5 drawdown window (8 losses, 3
wins). That's a real improvement. If we could apply the brake
SELECTIVELY to DOGE only, that would be net-positive for the
portfolio. But we can't know which symbol is about to lose when
the brake fires.

Alternative idea: **use each model's OWN running DD** instead of
portfolio DD. DOGE's brake fires when DOGE is in drawdown, not
when the portfolio is. Under this rule, DOGE's brake would still
fire during July-August 2025 (DOGE is leading the loss), but
SOL and NEAR's brakes would stay OFF because their per-symbol
running PnL is still positive during that window.

This is the **per-symbol brake** architecture, and it's the
recommended direction for iter-v2/014.

## The MERGE checklist — what passed and what failed

| Constraint | Target | Actual | Pass? |
|---|---|---|---|
| 10-seed mean Sharpe ≥ +1.1 | +1.1 | **+1.1458** | PASS |
| ≥ 7/10 profitable | 7 | **9** | PASS |
| OOS trades ≥ 50 | 50 | 117 | PASS |
| Primary seed MaxDD < 25% | 25% | **16.41%** | PASS |
| DSR > +1.0 | 1.0 | **+8.51** | PASS |
| IS/OOS ratio > 0 | 0 | **+13.98** | PASS |
| **Concentration (weighted) ≤ 50%** | **50%** | **78.55%** | **STRICT FAIL** |

Six checks pass, one strict-fails. The concentration rule is a
hard rule. NO-MERGE.

## Exploration/Exploitation Tracker

- iter-v2/001: EXPLORATION
- iter-v2/002: EXPLOITATION
- iter-v2/003: EXPLOITATION (NO-MERGE)
- iter-v2/004: EXPLOITATION
- iter-v2/005: EXPLORATION
- iter-v2/006: EXPLOITATION (NO-MERGE)
- iter-v2/007: EXPLOITATION (NO-MERGE)
- iter-v2/008: EXPLORATION (NO-MERGE)
- iter-v2/009: EXPLOITATION (NO-MERGE)
- iter-v2/010: EXPLORATION (NO-MERGE)
- iter-v2/011: EXPLORATION (cherry-pick, analysis)
- iter-v2/012: EXPLOITATION (cherry-pick, feasibility)
- **iter-v2/013: EXPLOITATION (NO-MERGE, concentration fail)**

Rolling 13-iter: 5 EXPLORATION / 8 EXPLOITATION = **38% exploration**.
Still above the 30% floor.

Six consecutive NO-MERGEs now (006-010, then 013). 011 and 012 were
cherry-picks (analysis milestones), not NO-MERGEs in the normal sense.

## Next Iteration Ideas

### iter-v2/014 — Per-symbol drawdown brake (RECOMMENDED)

Implement the brake as a per-symbol state tracked inside each
`RiskV2Wrapper` instance. Requires a small engine change:

1. Add `on_trade_closed(result: TradeResult)` to the Strategy
   Protocol (optional, called via `hasattr`).
2. Modify `run_backtest` to call `strategy.on_trade_closed(result)`
   after each trade closes.
3. `RiskV2Wrapper.on_trade_closed`: updates `self._shadow_equity`
   and `self._shadow_peak` for THIS wrapper's single symbol.
4. `RiskV2Wrapper.get_signal` consults the per-symbol brake state
   after the existing 4 gates and before vol scaling.

With per-symbol state, DOGE's brake fires on DOGE's DD only. SOL's
brake is separate. Cross-symbol contamination is impossible.

**Expected outcome**: DOGE gets its +14.5 improvement (brake saves
DOGE from July-August losses), SOL/NEAR keep their winners (their
brakes don't fire when their own models are up), XRP is unchanged.
Portfolio concentration stays near iter-v2/005's 47.75%. Aggregate
Sharpe drag is smaller than iter-v2/013's (because fewer winners
are killed).

### iter-v2/015 — BTC contagion circuit breaker (deferred primitive)

Primitive #6 from iter-v2/001. Kill v2 positions when BTC 1h/24h
drops below threshold. Complementary to per-symbol brake: catches
cross-symbol regime events (BTC crashes) that per-symbol DD can't
see because no individual model is yet in drawdown.

### iter-v2/016 — Validation upgrades (CPCV + PBO)

Deferred from iter-v2/001's skill. Adds rigor to hyperparameter
selection and expected-vs-realized Sharpe estimation. Lower
priority than risk-layer productionization but should land
before any paper-trading deployment.

### Recommendation

**iter-v2/014: per-symbol drawdown brake**. Same thresholds
(8%/16%), new architecture. Direct response to iter-v2/013's
failure mode. Highest expected value.

## MERGE / NO-MERGE

**NO-MERGE**. Concentration strict fail 78.55% > 50%.

Cherry-pick to `quant-research`:
- `briefs-v2/iteration_013/research_brief.md` (already committed)
- `briefs-v2/iteration_013/engineering_report.md`
- `diary-v2/iteration_013.md`
- `src/crypto_trade/strategies/ml/risk_v2.py` changes (the
  `DrawdownBrakeConfig`, `BrakeFireStats`, and
  `apply_portfolio_drawdown_brake` function — they're still
  useful for iter-v2/014 as a starting point, even though the
  runner usage will change)
- `run_baseline_v2.py` changes: **ROLL BACK** the brake wiring
  (iter-v2/014 will re-wire with per-symbol architecture).

**iter-v2/005 remains the v2 baseline.**

**Six consecutive NO-MERGEs on iteration branches (006-010,
013)**. The "3+ consecutive NO-MERGE" rule mandates a full
research checklist on the next iteration. iter-v2/014's brief
will cover Categories A-I explicitly.
