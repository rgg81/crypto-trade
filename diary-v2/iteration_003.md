# Iteration v2/003 Diary

**Date**: 2026-04-13
**Type**: EXPLOITATION (DOGE ATR multiplier specialization)
**Track**: v2 — diversification arm
**Branch**: `iteration-v2/003` on `quant-research`
**Parent baseline**: iter-v2/002 (OOS Sharpe +1.17 primary, +0.96 10-seed mean)
**Decision**: **NO-MERGE** — primary metric fails (+0.85 < +1.17),
pre-registered failure mode (IS-overfit) confirmed on single-seed.
10-seed validation skipped; see engineering report §"Why the 10-seed
validation was skipped".

## Results — side-by-side vs iter-v2/002 (primary seed 42)

| Metric | iter-v2/002 | iter-v2/003 | Δ | Outcome |
|---|---|---|---|---|
| **OOS Sharpe (weighted)** | **+1.172** | **+0.845** | **−0.327** | **FAIL** |
| OOS Sortino | +1.471 | +1.000 | −0.471 | — |
| OOS PF | 1.294 | 1.212 | −0.082 | PASS (>1.1) |
| OOS MaxDD | 54.63% | 50.10% | −4.5 pp | — |
| IS Sharpe | +0.538 | +0.449 | −0.089 | — |
| IS MaxDD | 68.80% | **102.20%** | +33.4 pp | **worse** |
| OOS trades | 139 | 126 | −13 | PASS (≥50) |
| v2-v1 OOS corr | +0.042 | ~same | — | PASS (<0.80) |

Primary metric fails by 0.33 Sharpe units. IS MaxDD blew up to 102%,
indicating the widened barriers let IS drawdowns run deeper before SL.

## DOGE per-symbol — the IS-overfit pattern (pre-registered)

**This is the key finding of iter-v2/003.**

| DOGE Metric | iter-v2/002 (2.9/1.45) | iter-v2/003 (4.0/2.0) | Δ |
|---|---|---|---|
| **IS** trades | 139 | 107 | −32 |
| **IS** WR | 42.4% | **48.6%** | **+6.2 pp** |
| **IS** raw PnL | +55.97% | **+86.80%** | **+30.83 pp** |
| **IS** avg PnL/trade | +0.40% | **+0.81%** | **2.0×** |
| **OOS** trades | 47 | 34 | −13 |
| **OOS** WR | 38.3% | **35.3%** | **−3.0 pp** |
| **OOS** raw PnL | −24.02% | **−32.14%** | **−8.12 pp** |
| **OOS** avg PnL/trade | −0.51% | **−0.95%** | **−87% worse** |

**IS doubled** per-trade. **OOS got 87% worse** per-trade. The wider
barriers fit the IS training distribution but don't generalize to OOS.

**SOL and XRP** per-symbol metrics: **byte-for-byte identical** to
iter-v2/002 (verified via gate stats and per-trade counts). The one-
variable isolation held perfectly — the aggregate regression is entirely
attributable to DOGE.

## Pre-registered failure-mode prediction — correctly anticipated

Brief §6.3 predicted: "DOGE IS raw PnL jumps substantially (e.g.,
+55.97% → +80%+) while DOGE OOS stays negative or worsens. The signal
would be a DOGE IS WR rise of +5pp or more with flat/worse OOS WR."

**Actual**:
- DOGE IS raw PnL: +55.97% → **+86.80%** ✓ (within predicted +80%+ range)
- DOGE IS WR: +6.2 pp ✓ (≥ 5 pp predicted)
- DOGE OOS WR: −3.0 pp ✓ (flat/worse predicted)
- DOGE OOS raw PnL: worse ✓

**The failure was correctly anticipated**. This is strong evidence that
the DOGE-multiplier-widening approach is directionally wrong for OOS
DOGE, not a noise artifact. Going to 10-seed validation would just
confirm this with more precision.

## Hard Constraints

| Constraint | Target | Actual | Pass? |
|---|---|---|---|
| Primary OOS Sharpe > +1.17 | +1.17 | **+0.845** | **FAIL** |
| ≥7/10 seeds profitable | — | 1/1 profitable (only ran 1) | N/A |
| OOS PF > 1.1 | 1.1 | 1.212 | PASS |
| OOS trades ≥ 50 | 50 | 126 | PASS |
| **No single symbol > 50% OOS PnL** | 50% | **XRP 121%, DOGE −103%** | **FAIL (worse than iter-v2/002)** |
| DSR > +1.0 | +1.0 | +11.85 | PASS (wide at N=3) |
| v2-v1 correlation < 0.80 | <0.80 | ~0.04 | PASS |
| IS/OOS Sharpe ratio > 0.5 | 0.5 | 1.88 | PASS |

**Primary fails. Concentration fails harder than iter-v2/002** (DOGE
is MORE negative, so the signed ratio is worse). No QR override
available — this would be the second use of the override for the same
concentration issue, which is not honest practice.

## Why the 10-seed validation was skipped

Per the v2 skill, 10-seed validation is mandatory before MERGING, not
before rejecting. The decision to NO-MERGE is made on the primary-seed
result because:

1. **Primary fails by 0.33 Sharpe** — a wide gap well above the ~0.20
   noise floor seen in iter-v2/002's 10-seed std of 0.60.
2. **Failure mode is pre-registered and confirmed** — DOGE IS-overfit
   pattern exactly as predicted in brief §6.3. The hypothesis is
   directionally wrong; more seeds would confirm, not reverse.
3. **Seed 42 is typically above median**. In iter-v2/002's 10-seed
   sweep, seed 42 was ABOVE mean (+1.17 vs +0.96). If seed 42 is
   already below baseline in iter-v2/003, the 10-seed mean will be
   even further below baseline.
4. **Compute discipline**: 40 min of compute for a clearly-wrong
   hypothesis is wasteful. iter-v2/004 (low-vol filter) has a
   structurally more promising target (the −1.86 Sharpe low-vol
   bucket) and should be prioritized.

## Exploration/Exploitation Tracker

- iter-v2/001: EXPLORATION (new infra)
- iter-v2/002: EXPLOITATION (risk config)
- iter-v2/003: EXPLOITATION (DOGE specialization)

Rolling 10-iter exploration rate: 1/3 = 33% — meets the 30% minimum.
iter-v2/004 can be exploit or explore; the low-vol filter is a risk-
config tune so it's exploit. iter-v2/005 should probably be explore
(e.g., replace DOGE with NEAR — that's a symbol universe change, which
counts as EXPLORATION per the skill).

## Lessons Learned

1. **Pre-registered failure-mode predictions work**. I wrote the brief
   saying "the most likely failure is DOGE IS-overfit". The failure
   happened exactly that way. This is strong evidence that the
   Risk Management Design Section 6 discipline adds real value — it
   focuses attention on the mechanism, not just the outcome.

2. **DOGE's meme dynamics are not fixable by wider ATR barriers**.
   Wider barriers let IS-era DOGE runs produce bigger wins (those
   2020-2021 meme rallies get fully captured), but in the OOS 2025
   DOGE regime, the wider SL just lets losing trades run longer. The
   TRUE fix is either (a) labeling strategy change (ternary, event-
   driven), (b) different model architecture per DOGE, or (c) replacing
   DOGE with a less-meme-like symbol.

3. **Isolation testing works**. SOL and XRP were byte-for-byte
   identical to iter-v2/002 because the per-model multiplier change
   was truly isolated. This makes NO-MERGE attribution clean: the
   regression is 100% DOGE's fault.

4. **Don't fight the data**. iter-v2/002's DOGE weighted Sharpe was
   −0.31. I treated DOGE as "fixable" with a parameter tweak. It
   isn't. The signal quality on DOGE is genuinely lower than SOL/XRP.
   Next step should either fix something else (low-vol filter) or
   replace DOGE entirely.

5. **First-seed fail-fast works when the failure mode matches the
   prediction**. Saved 40 min of compute.

## lgbm.py Code Review

No changes needed. The runner's per-model multiplier plumbing works
correctly — verified by SOL/XRP being byte-for-byte identical to
iter-v2/002 while DOGE's metrics changed. The parameter flows through
`_build_model(atr_tp_multiplier, atr_sl_multiplier)` into
`LightGbmStrategy.atr_tp_multiplier` and from there into labeling.

## Next Iteration Ideas

### Priority 1 (iter-v2/004): Low-vol filter

**This is the iter-v2/002 diary's Priority 2 idea, promoted to
Priority 1 after iter-v2/003's DOGE multiplier dead-end.**

Add `atr_pct_rank_200 >= 0.33` as an entry condition in
`RiskV2Wrapper.get_signal` — skip signals when the current bar is in
the bottom third of the ATR percentile distribution. This kills the
low-vol trending bucket which had weighted Sharpe −1.86 in iter-v2/002.

Expected outcome: the 54 low-vol OOS trades (all 3 symbols) are
removed. Remaining 85 trades have weighted mean (0.81 × 43 + 1.49 × 42) / 85
≈ +1.14 Sharpe (estimated from iter-v2/002's per-bucket breakdown).
Aggregate OOS Sharpe could land in +1.3 to +1.6 range.

Caveat: removing 54 trades brings OOS trade count from 139 → 85.
Still above the 50 minimum but tighter.

**One variable change**: add a new gate to `RiskV2Wrapper`. Keep DOGE
on 2.9/1.45 (revert iter-v2/003's change). Keep everything else
identical to iter-v2/002.

### Priority 2 (iter-v2/005 if low-vol filter doesn't fix concentration): Replace DOGE with NEARUSDT

From iter-v2/001's screening, NEARUSDT was the fourth-strongest candidate
(v1 corr 0.665, ~4,847 IS rows, $240M/day volume, L1 category). Swap
Model E from DOGE to NEAR. This fixes the concentration caveat by
removing DOGE (the negative contributor) and adding a new positive-
expected-value symbol.

Caveat: losing DOGE raises v2's v1 correlation (DOGE was the lowest-
corr pick at 0.51, NEAR is 0.67). Still well under the 0.80 limit but
a modest diversification trade-off.

### Priority 3 (iter-v2/006): Lower ADX threshold 20 → 15

iter-v2/002 kill rate was 45-51% combined, 28% from ADX alone. Lower
ADX threshold would reduce ADX firing to ~10% and bring combined kill
rate into the 20-30% target band. Could recover 5-10% more signal and
raise OOS Sharpe further.

### Deferred (iter-v2/007+)

- Bump Optuna trials 10 → 25
- Enable drawdown brake
- Enable BTC contagion circuit breaker

## MERGE / NO-MERGE

**NO-MERGE**. Cherry-pick research brief + engineering report + this
diary to `quant-research`. iter-v2/003 branch stays as a record. No
BASELINE_V2.md update. No tag. The code change (per-model ATR multipliers
plumbing in `run_baseline_v2.py`) stays on the branch too — iter-v2/004
will create its own branch from `quant-research` and not need the
multiplier plumbing (unless iter-v2/005's DOGE replacement uses it,
in which case it will be re-introduced at that time).

iter-v2/002 remains the v2 baseline: OOS Sharpe +1.17 (primary), +0.96
(10-seed mean), 9/10 profitable, v2-v1 correlation +0.042. iter-v2/004
targets +1.17 or better.
