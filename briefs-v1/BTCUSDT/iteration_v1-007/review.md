# Phase 7.5 Critic Review — iter-v1/007 (BTCUSDT) — EXPLORATION screen

## Verdict: NEGATIVE — OI non-linear signal absent; ORTHOGONAL-FEATURE AXIS CLOSED for BTC.

### Results (K=5 screen)
| | IS Sharpe | OOS Sharpe | ratio | dispersion | IS net | OOS net | trades | OI rank |
|---|---|---|---|---|---|---|---|---|
| iter-004 prune-only (K=20) | −0.17 | +0.48 | −2.82 (inv) | — | — | — | — | n/a |
| iter-007 prune+OI-delta (K=5) | **−0.4723** | **−0.0266** | **+0.06 (both neg)** | 42.42 | −20.08 | −0.33 | 191/84 | **29/42** |

### Critic's literal read
Both-negative, IS worst-of-batch (−0.47). The OI feature trained (rank 29/42, no silent drop —
verifiability fix) but contributed nothing usable; the non-linear OOF-lift hypothesis did not
survive the bagged specialist. **NEGATIVE.** Not mergeable.

### The axis-closure call is sound
Three orthogonal families tested live (funding spread, funding level, OI), every added feature at
bottom-third importance (ranks 16, 29, 29), every profile negative or inverted. FE IS-only
pre-screen rules out the rest (basis degrades, long/short zero-IC, cross-asset dead). The orthogonal
-feature lever cannot rescue a base signal at the noise floor (max |IS-IC| 0.028). Closing the axis
is the correct, evidence-backed call — not premature abandonment.

### Methodology PASS
- Honest costs, IS/OOS split, full data, 5/5 seeds (275 trades). OOS-vigilance: no new OOS-touching
  analysis; reused the verified IS-only FE script.

## Proposed Backtest Changes (mandatory)
1. **iter-v1/008 — PIVOT AXIS to labeling/horizon.** Current label = ATR triple-barrier (tp 2.9 /
   sl 1.45 ATR, 7-day timeout). Test whether BTC has a more learnable target: a longer timeout, a
   `fixed_horizon` label at a longer N-candle horizon (the FE saw funding IC strengthen 1-bar→3-bar:
   −0.057→−0.070), or `trend_scanning`. QR designs on IS-only purged-CV signal evidence.
2. **Parallel candidate — regime gate.** If labeling shows no lift, gate trades to the regime where
   BTC's conditional IS edge is positive (trend/vol state), removing noise-floor regimes. QR should
   measure the conditional-IS edge IS-only before committing.
3. **Escalation criterion (pre-registered):** if BOTH the labeling pivot (iter-008) AND a regime gate
   fail to produce a coherent (both-positive) IS edge for BTC, escalate to the user the evidence that
   BTC at 8h may not be tractable with this architecture, and propose a symbol pivot. Seven iterations
   of negative/inverted IS + a closed orthogonal axis + a noise-floor IC is a strong prior that BTC is
   the wrong FIRST symbol — but the labeling/regime levers must be ruled out first.
