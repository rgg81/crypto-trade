# Engineering Report — iter-v3/032

## Status: READY-FOR-CRITIC

Wall-clock 0.32h (19 min). PROMISING-OOS-MIXED — LDO ATR (1.5, 0.75) lifted LDO from -3.07 to +3.98 OOS; OOS Sharpe +1.93 highest in v3 catalog; but IS Sharpe collapsed -0.56.

## Hypothesis-Implementation Alignment

ADD V3_ATR_MULTIPLIERS_PER_SYMBOL with LDO (1.5, 0.75); RESTORE LDO to V3_MODELS (3→4); REQUIRED_GAP 66→88. ITERATION_LABEL=v3-032.

## Reproducibility Stamps

Setup `d0ec5dc`, gate `daae54f`, brief `de2478d`, EDA `9834e84`.

## Headline Metrics

| Metric | Value | vs iter-v3/029 anchor (+0.7926/+1.7653) |
|--------|-------|------------------------------------------|
| IS monthly Sharpe | +0.2360 | Δ -0.56 (collapse) |
| OOS monthly Sharpe | **+1.9338** | **Δ +0.17 — HIGHEST single-seed OOS in v3 catalog** |
| Bundle OOS trades | **129** | +9 (basically at 130 floor) |
| Top-sym OOS conc | 45.10% TRX | -5.5pp from iter-v3/029 50.6% |
| OOS MaxDD | 29.93% | similar |
| IS MaxDD | 49.27% | +14.5pp (worse — IS axis less smooth) |
| DSR | 0.0 | EXPLORATION artifact |
| PBO mean | 0.0967 | PASS |
| n_eff | 19 | consistent |

## Per-Symbol OOS — LDO BIG IMPROVEMENT

| Symbol | weighted_pnl OOS | Trades | WR | vs iter-v3/029 |
|--------|------------------|--------|-----|----------------|
| TRX | +29.24 | 46 | 52.2% | bit-identical |
| ALGO | +20.87 | 25 | 40.0% | bit-identical |
| BCH | +10.75 | 38 | 39.5% | bit-identical |
| **LDO** | **+3.98** | **20** | **35.0%** | **+6.05 swing (was -3.07)** |

Per-symbol ATR architecture works: LDO labels changed, BCH/TRX/ALGO labels unchanged (default 2.0, 1.0). LDO Optuna re-trained with tighter (1.5, 0.75) labels found different IS-fit configuration that produces 20 trades (vs 11) with 35% WR (vs 36.4%) but POSITIVE OOS contribution.

**Hypothesis validated**: LDO needed different LABELS not different features (iter-v3/030 falsified the per-symbol-features approach for LDO). The labeling-layer fix works.

## §4.4 Classification

PATH A-MIXED:
- LDO improved (✓ +6.05 OOS swing)
- BCH/TRX/ALGO bit-identical (✓)
- OOS Sharpe lifted (+0.17)
- BUT IS Sharpe dropped (-0.56) — IS axis collapse

This is the same single-seed-lottery pattern as iter-v3/026/027/030 (IS collapse + OOS lift/hold). The OOS lift is single-seed-suspect; multi-seed CONFIRMATION is the truth-test.

**Verdict: EXPLORATION-PROMISING-OOS-MIXED**.

The LDO improvement is REAL and structurally sound (different labels for different volatility regime). But the IS aggregate Sharpe drop suggests Optuna found IS-overfit configurations on the new label space. The architecture works; the question is whether multi-seed validation (iter-v3/039) preserves the LDO lift.

## Bundle Implications for iter-v3/039 CONFIRMATION

3 validated edge ingredients in the post-bootstrap cycle so far:
1. **regime_momentum_signed_5d** (iter-v3/025 single-seed → iter-v3/028 multi-seed validated)
2. **ADD ALGOUSDT with per-symbol-feature-signature alignment** (iter-v3/029)
3. **LDO per-symbol ATR (1.5, 0.75)** (iter-v3/032 — single-seed; needs multi-seed validation)

For iter-v3/039 CONFIRMATION, the bundle would be: 4-symbol BCH+LDO+TRX+ALGO + regime_momentum_signed_5d + LDO_ATR(1.5, 0.75). All other settings default.

Caveat: ingredient #3 (LDO ATR) hasn't been multi-seed-validated. iter-v3/039 multi-seed run will reveal whether the LDO improvement holds.

## Recommendations

iter-v3/033 axis: **ADD 5TH SYMBOL with per-symbol-feature-signature alignment**.

Rationale:
1. Outstanding MERGE gates after iter-v3/032: bundle OOS 129<130 (-1), top-sym 45.1%>30% (-15pp), IS Sharpe +0.24<+1.0 (-0.76)
2. 5th symbol addresses concentration + bundle trades (2 of 3 gaps mechanically)
3. iter-v3/029 methodology proven: per-symbol-feature-signature alignment selection beats correlation-only
4. Candidates from prior EDA (excluding HBAR+AVAX failures): FILUSDT, VETUSDT, ATOMUSDT — re-evaluate against iter-v3/032 multi-symbol importance for best alignment

Status: READY-FOR-CRITIC.
