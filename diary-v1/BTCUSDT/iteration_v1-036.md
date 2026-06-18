# Diary — iter-v1/036 (BTCUSDT) — EXPLORATION — PORTABILITY of the strip-the-model breakthrough — PROMISING-PARTIAL (directional confirm; mixed net vs iter-020 → NO-MERGE)

**Axis:** portability of the iter-034/035 ETH breakthrough — apply `deterministic_entry_only=True` (STRIP
the overfit LightGBM entry layer; enter every conviction-gated candle in the trend-state direction) to
the BTC iter-020 stack. Single axis vs iter-020. K=1 (model bypassed → K-invariant; dispersion=0).

**Result: IS Sharpe +0.2977 / OOS +0.1153** (ratio 0.39). 78 IS / 38 OOS trades, WR 25.6%/31.6%,
PF 1.23/1.06, OOS MaxDD 4.12%, dispersion=0.

## Verdict: PROMISING-PARTIAL — the finding ports DIRECTIONALLY but is a mixed trade on BTC → NO-MERGE.
vs BTC baseline iter-020 (IS +0.37 / OOS +0.09, K=20 model):
- **OOS: BETTER (+0.09 → +0.1153, +28%)** — same direction as ETH (+0.056→+0.41). **The model drags OOS
  on BOTH coins** — the core finding (LightGBM entry layer is overfit, hurts OOS) GENERALIZES directionally.
- **IS: WORSE (+0.37 → +0.2977, −0.07)** — UNLIKE ETH (where IS held +0.63→+0.65). On BTC the model adds
  REAL IS value (some learned structure), so stripping it is an IS−/OOS+ TRADE, not a clean Pareto-win.
- **NOT Pareto-dominant** vs iter-020 (worse IS, better OOS). The OOS gain (+0.025) does not clearly
  outweigh the IS loss (−0.07). Conservative call: do NOT replace the established K=20-confirmed iter-020
  baseline on a mixed single-axis result. **iter-020 STAYS BASELINE_V1_BTCUSDT.**

## The coin-dependent nuance (track-level finding)
The strip-model EFFECT is real on both coins (OOS improves), but its NET VALUE is coin-dependent:
- **ETH (iter-034): model was PURE DRAG** — stripping it held IS (+0.65) AND lifted OOS 7.4× (+0.41).
  ETH's LightGBM entry layer learned almost-entirely-overfit IS setups → clean win.
- **BTC (iter-036): model adds IS but drags OOS** — stripping it costs IS (−0.07) for a modest OOS lift
  (+0.025). BTC's model is LESS overfit (it learned some real IS structure) → mixed trade.
Interpretation: the model's IS edge that does NOT translate to OOS is overfit; the share that's overfit
varies by coin (ETH ≈ all of it; BTC ≈ part). The deterministic core is the robust floor across coins;
the model adds variable (often net-negative on OOS) value.

## OOS-vigilance + rigor
Deterministic (model bypassed; same look-ahead-tested gate + trend-state primitives as iter-034, 67 tests
pass). dispersion=0 → K-invariant (no lottery). OOS seen first in this eval; NO-MERGE is on the
IS-regression / not-Pareto-dominant basis, not an OOS fit.

## Next
The strip-model finding is now confirmed DIRECTIONALLY on 2 coins (ETH clean win + merged; BTC OOS-lift
but mixed). The track-level hypothesis — "the deterministic core generalizes; the LightGBM entry layer is
variably overfit and OOS-negative" — is worth mapping across the remaining coins (LINK/LTC/DOT) to decide
whether the v1 architecture should default to the model-stripped deterministic core. Each needs a baseline
bootstrap first. Alternatively: a BLEND (partial model influence) to capture BTC's IS while keeping the
OOS lift — a new mechanism. ETH (iter-034) remains the headline win; BTC iter-020 stays its baseline.
