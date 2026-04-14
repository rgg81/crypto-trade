# Iteration v2/014 Engineering Report

**Type**: FEASIBILITY STUDY (per-symbol drawdown brake)
**Role**: QE
**Date**: 2026-04-14
**Branch**: `iteration-v2/014` on `quant-research`
**Parent baseline**: iter-v2/005 (47.75% XRP, 10-seed mean +1.297)
**Decision**: **NO-MERGE** (all 4 configs fail concentration; structural XRP dominance)

## Run Summary

| Item | Value |
|---|---|
| Runner | `analyze_per_symbol_brake.py` (commit `96d69ce`) |
| Input | `reports-v2/iteration_v2-005/out_of_sample/trades.csv` (117 trades) |
| Wall-clock | <2 sec |
| Artifacts | `reports-v2/iteration_v2-014_per_symbol_brake/` |

## Headline table — all 4 configs FAIL

| Config | Sharpe (trade) | Sharpe (daily) | MaxDD | Calmar | PnL | **MaxConc** | NegFlip |
|---|---|---|---|---|---|---|---|
| **None (baseline)** | **+1.66** | **+3.35** | **−45.33%** | +2.61 | +94.01% | **47.75%** | no |
| A (5/10) | +1.18 | +2.36 | −19.35% | +2.38 | +45.13% | **92.65%** | YES |
| B (6/12) | +0.90 | +1.80 | −28.20% | +1.14 | +35.69% | **113.12%** | YES |
| C (8/16) | +1.35 | +2.67 | −27.84% | +2.31 | +59.66% | **71.80%** | YES |
| **D (4/8)** | **+1.45** | **+2.90** | **−13.83%** | **+4.31** | +53.59% | **68.76%** | **no** |

**Rule**: MaxDD < 25% AND Sharpe_trade > 1.3 AND MaxConc < 55% AND no negative flip.

- Config A: fails Sharpe, concentration, flip
- Config B: fails MaxDD, Sharpe, concentration, flip
- Config C: fails MaxDD, concentration, flip
- Config D: **closest** — passes MaxDD, Sharpe, flip, but fails concentration (68.76% vs 55% rule)

**Not a single config passes.**

## Root cause — XRP per-symbol DD never fires

The per-symbol brake's decision is based on each symbol's OWN
compound equity DD. XRP's per-symbol OOS curve is near-monotone
up (27 trades, 55.6% WR, +44.89 weighted PnL), so XRP's
per-symbol running DD almost never hits the 4-8% threshold.

**Per-symbol brake firings (Config D 4/8)**:

| Symbol | Normal | Shrink | Flatten | Fire rate |
|---|---|---|---|---|
| DOGE | 7 | 1 | **23** | **77%** |
| SOL | 11 | 7 | 19 | 70% |
| NEAR | 7 | 5 | 10 | 68% |
| **XRP** | **21** | **5** | **1** | **22%** |

**Result**: XRP keeps 78% of its baseline contribution (from 44.89
to 36.85) while DOGE/SOL/NEAR get heavily attenuated. The ratio of
XRP's preserved contribution to the total portfolio contribution
grows to 68.76%.

**The brake is correctly identifying drawdowns**, but the
drawdowns are concentrated in DOGE/SOL/NEAR, not XRP. So the
brake's attenuation is asymmetric by design, which maps to a
concentration blow-up.

## Why per-symbol is WORSE than portfolio brake for concentration

Comparing iter-v2/013 (portfolio brake) with iter-v2/014 Config C
(per-symbol brake):

| Metric | Baseline | iter-v2/013 portfolio C | iter-v2/014 per-symbol C |
|---|---|---|---|
| Sharpe (trade) | +1.67 | +1.60 | +1.35 |
| MaxDD | −45.33% | −16.41% | −27.84% |
| XRP weighted share | 47.75% | 78.55% | **71.80%** |
| XRP weighted PnL | +44.89 | +46.84 | **+42.84** |
| DOGE weighted PnL | +11.52 | +26.06 | +5.19 |
| SOL weighted PnL | +28.89 | −0.18 | +14.24 |
| NEAR weighted PnL | +8.71 | −13.08 | −2.60 |

**Per-symbol brake affects all symbols more uniformly**, so XRP's
absolute PnL drops from 44.89 to 42.84 (vs portfolio brake which
left XRP at 46.84). But DOGE/SOL/NEAR drop more too, so the
ratio is still bad.

**Per-symbol brake's Sharpe/MaxDD is WORSE than portfolio brake's.**
Config C (per-symbol) Sharpe +1.35, MaxDD −27.84%, vs iter-v2/013
Sharpe +1.60, MaxDD −16.41%. Per-symbol fires more aggressively
because single-symbol DDs hit 8% faster than aggregated portfolio
DDs.

Both designs fail concentration, and per-symbol is strictly
worse on aggregate metrics. **Neither works.**

## The structural XRP dominance problem

iter-v2/005 has XRP at 47.75% weighted share — 2.25 pp below the
50% strict limit. This is the closest iter-v2 has come to the
concentration ceiling in any MERGEd iteration.

Any intervention that attenuates the OTHER symbols will push
XRP's relative share UP. The brake can attenuate:
- **DOGE** (losses during July-August) → helps net PnL, raises XRP share
- **SOL** (winners during July-August) → hurts net PnL, raises XRP share
- **NEAR** (mix during July-August) → mixed, but typically raises XRP share
- **XRP** itself → lowers XRP share, but XRP rarely DDs

The brake only effectively fires on DOGE/SOL/NEAR because XRP
doesn't DD. Therefore concentration always gets worse.

### Fundamental conclusion

**The drawdown brake lineage (iter-013 portfolio + iter-014
per-symbol) is incompatible with this 4-symbol portfolio because
XRP's contribution is too dominant.** Any attenuation that
preserves XRP while trimming others worsens concentration.

The only brake designs that could preserve concentration would:
1. Attenuate XRP SPECIFICALLY when it's growing too fast (a peak
   brake, not a DD brake) — but this is a rebalancing primitive,
   not a risk primitive
2. Use SYMMETRIC attenuation (not differential) — but then no
   symbol-specific defence is possible

Neither is a small modification of the current brake code.

## Pre-registered failure-mode prediction — partially correct

Brief §"Pre-registered failure-mode prediction":

> **"Per-symbol DD is too noisy to brake effectively. Each model
> has only 20-40 OOS trades. The compound equity of a single
> model can be −8% after just 2-3 bad trades, triggering shrink
> on legitimate vol."**

**Actual**: DOGE hits flatten threshold after 2-3 bad trades and
stays flattened for the entire July-August stretch. SOL and NEAR
also hit shrink on small per-symbol DDs. Exactly as predicted.

> **"Sweet spot prediction: Config C still wins."**

**Actual**: Config D (4/8) is closest to passing, not Config C.
The prediction was wrong because I underestimated how much
per-symbol DDs amplify noise.

> **"Concentration stays near baseline 47.75%."**

**Actual**: Concentration blows out to 68-113% depending on config.
The prediction completely missed the XRP dominance failure mode.

## Hard-constraint check

| Constraint | Target | Best (D 4/8) | Pass? |
|---|---|---|---|
| OOS MaxDD < 25% | 25% | 13.83% | PASS |
| OOS Sharpe (trade) > 1.3 | 1.3 | +1.45 | PASS |
| **Concentration ≤ 55%** | **55%** | **68.76%** | **FAIL** |
| No negative-flip per-symbol | 0 | 0 | PASS |
| OOS PF > 1.3 | 1.3 | not computed per config | — |

Three of four pass for Config D. Concentration is the blocker.

## Label Leakage Audit

No backtest, no models trained. No leakage possible.

## Code Quality

- `analyze_per_symbol_brake.py` is 280 lines, single responsibility,
  type-hinted
- Reads iter-v2/005 OOS trades from disk, applies 4 configs
  post-hoc, writes artifacts
- No production code touched. `risk_v2.py` still has the
  portfolio brake primitives from iter-v2/013 (which can stay
  unused for now)
- Lint clean

## Recommendation: abandon the drawdown brake lineage

After 3 iterations targeting the drawdown brake primitive:

1. **iter-v2/012** (feasibility, portfolio brake): PASS on
   aggregate, concentration not tested
2. **iter-v2/013** (productionize portfolio brake): NO-MERGE,
   concentration 78.55%
3. **iter-v2/014** (feasibility, per-symbol brake): NO-MERGE,
   concentration 68.76% (best of 4 configs)

The core issue is **structural**: XRP's dominance means any brake
that differentially affects non-XRP symbols will blow out
concentration. This is not a tunable problem.

**What works instead** (pivot directions for iter-v2/015+):

### Option 1 — BTC contagion circuit breaker (deferred primitive #6)

Unconditionally kills ALL positions when BTC moves below a
threshold (e.g., BTC 1h < −5%). Affects every symbol uniformly
in proportion to the signal, not to symbol-specific DD. Should
preserve concentration better because all symbols experience
the same attenuation window.

### Option 2 — 5th symbol to dilute XRP

Add a 5th v2 symbol (Model I) chosen to reduce XRP's dominance.
The existing 6-gate screening identified AVAX, UNI, ADA as
candidates with v1 corr < 0.85 and adequate volume. An AVAX or
UNI model would add 20-30 trades and could drop XRP share to
~40%.

### Option 3 — Accept iter-v2/005 as final v2 baseline

The 4th-symbol ceiling is real (iter-v2/006-010 established).
The drawdown brake ceiling is real (iter-v2/012-014 established).
iter-v2/005 with its +1.297 Sharpe / 59.88% MaxDD / 47.75%
concentration IS the achievable v2 baseline for this
configuration. Paper-trading and combined-portfolio deployment
become the next-value work.

### Option 4 — Validation rigor (CPCV + PBO)

Deferred from iter-v2/001's skill. Doesn't improve the baseline
but quantifies the honest expected-vs-realized gap. Gatekeeper
for any live deployment.

### Recommended next

**Option 1 (BTC contagion)**. It's the only unexplored risk
primitive that DOESN'T run into the XRP dominance problem.
Feasibility can be a post-hoc simulation against BTC's 1h data,
then productionize if it works.

## Conclusion

iter-v2/014's per-symbol brake feasibility **fails all 4
configurations** on the concentration rule. The best config (D
4/8) achieves strong aggregate metrics (Sharpe +1.45, MaxDD
−13.83%, Calmar +4.31) but 68.76% XRP concentration is
unacceptable.

Combined with iter-v2/013's portfolio brake failure, the
drawdown brake lineage is definitively closed for this 4-symbol
v2 portfolio. XRP's dominance is a structural constraint that
cannot be engineered around with brake architecture changes.

**Decision**: **NO-MERGE**. Cherry-pick the research brief +
engineering report + diary + `analyze_per_symbol_brake.py` to
`quant-research`. iter-v2/005 remains the v2 baseline.

iter-v2/015 should pivot to the BTC contagion circuit breaker or
to validation rigor upgrades (CPCV + PBO).
