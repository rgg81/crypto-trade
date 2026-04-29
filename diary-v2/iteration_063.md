# iter-v2/063 Diary

**Date**: 2026-04-23
**Type**: EXPLOITATION (5th symbol added, config else unchanged)
**Parent baseline**: iter-v2/059-clean
**Decision**: **NO-MERGE** — AAVE net −21 wpnl OOS, overall OOS −35%

## Hypothesis vs result

**Hypothesis**: adding AAVEUSDT as a 5th symbol mechanically dilutes NEAR's
57.96% concentration.

**Result**: NEAR DID dilute (57.96% → 44.44%, −13.5pp). **But** AAVE itself
lost hard (−21.34 OOS wpnl, 26.1% WR), and the total OOS PnL shrank enough
that the overall Sharpe collapsed by 35%.

| Metric | iter-v2/059-clean | iter-v2/063 | Δ |
|---|---|---|---|
| IS monthly Sharpe | +1.04 | **+1.14** | +9% |
| OOS monthly Sharpe | +1.66 | +1.07 | −35% |
| Combined monthly | 2.70 | 2.21 | −18% |
| OOS PF | 1.78 | 1.35 | −24% |
| OOS MaxDD | 22.61% | 31.54% | +39% (worse) |
| NEAR concentration | 57.96% | 44.44% | −13.5pp (improved, still FAILs n=5 cap of 40%) |

## Pre-registered failure-mode check

The brief's Section 6.3 predicted: *"AAVE could strengthen NEAR's regime
dominance instead of diluting. Failure signature: AAVE OOS <5% positive
contribution AND NEAR >55%."*

**Actual failure differed**: AAVE didn't just contribute little — it
contributed NEGATIVELY (−21.34 wpnl, 23 OOS trades, 26% WR). NEAR dropped
to 44%, so dilution worked. The REAL failure was the one I didn't
pre-register: **AAVE loses money in its OOS regime**.

This matches the skill's documented "known-unknown failure mode" exactly:
*"slow monotone grind-down that never triggers ATR percentile spikes nor
feature z-score excursions."* AAVE traded often (23 OOS trades — more than
DOGE, XRP, or NEAR), all within the v2 risk gates' acceptance region, just
with poor directional accuracy (26% WR).

## Why AAVE failed where iter-v2/001-v2/059 picked profitable symbols

The earlier profitable symbols (DOGE, SOL, XRP, NEAR) passed a proper
**Gate 3** (stand-alone profitability screening) before entering v2.
iter-v2/063's brief **explicitly skipped Gate 3** for speed, noting it as
"deferred for autopilot exploitation." That was the wrong call. AAVE's IS
LGBM looked fine (50% WR, +25 IS PnL) but that's just because LGBM finds
patterns in most crypto IS data; the OOS test is where Gate 3 actually
pays off.

**Lesson**: never skip Gate 3 when adding a symbol, even for exploitation
iterations. 30min of Gate 3 compute would have flagged AAVE as marginal.

## MERGE criteria evaluation

| # | Criterion | Target | Actual | Pass |
|---|---|---|---|---|
| 1 | Combined IS+OOS monthly Sharpe | ≥ 2.70 | 2.21 | FAIL |
| 2 | NEAR concentration | <45% | 44.44% | PASS (barely) |
| 3 | OOS monthly Sharpe ≥ 0.85 × baseline | ≥ 1.41 | 1.07 | FAIL |
| 4 | IS monthly Sharpe ≥ 0.85 × baseline | ≥ 0.88 | 1.14 | PASS |
| 5 | OOS trade Sharpe > 0, PF > 1, trades ≥ 50 | — | 1.17 / 1.35 / 80 | PASS |
| 6 | Per-seed max ≤ 40% (n=5) | ≤ 40% | 44.44% | FAIL |
| 7 | v2-v1 correlation < 0.80 | <0.80 | not measured | — |

4 FAILs → **NO-MERGE**.

Follow skill's NO-MERGE flow: cherry-pick 3 doc commits (research brief,
engineering report, this diary) to `quant-research`. Code commit
`3cf459a` stays on `iteration-v2/063` permanently. Run the post-NO-MERGE
audit to confirm no code leaked.

## Next Iteration Ideas — iter-v2/064

Ordered by priority + feasibility:

### 1. (primary) Gate 3 screening of candidate 5th symbols, then retry
Run stand-alone LGBM Gate 3 on BCH, UNI, FIL, TRX, RUNE (candidates that
passed Gates 1-2 but weren't screened for Gate 3). Pick the top-1 with IS
Sharpe > 0.5 AND OOS proxy (if possible) — deliberately avoid the AAVE
mistake.

Expected compute: 5 × 30min = 2.5h for Gate 3; then 2.5h for the baseline
run if a symbol passes. Total: ~5h for one more iteration.

### 2. (alternative) Per-symbol position cap at backtest layer
iter-v2/059-clean's NEAR share is ceiling-less. Add a concentration gate
to RiskV2Wrapper: if NEAR's cumulative recent wpnl is >40% of portfolio
total, size NEAR signals at 0.5x or kill. This is the skill's priority
#3 fix. Requires modifying RiskV2Wrapper + tracking portfolio state
across trades. More engineering than option 1 but fixes the problem
mechanically (no need to find a magical 5th symbol).

### 3. (alternative) Optuna trials reduction 50 → 25
Worked iter-v2/028 → iter-v2/029 for XRP dominance. Cheap. But less likely
to help here since NEAR's dominance is from GENUINE performance, not
over-selective Optuna.

### 4. Drop a weak symbol instead
DOGE (7.2% share, 43.8% WR) or SOL (14.8% share, 38.9% WR) are the weak
contributors. Dropping to 3 symbols changes n=3 thresholds (max 55%),
which NEAR's 57.96% still doesn't pass but would with marginal dilution.
Probably the wrong direction.

**Recommended next iteration**: option 1 (proper Gate 3 screening). If
that also fails to find a good 5th symbol, move to option 2 in
iter-v2/065.
