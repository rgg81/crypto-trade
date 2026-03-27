# Iteration 050 — EXPLORATION (balanced class weights, retry of 048)

## NO-MERGE: OOS Sharpe +1.66 (best ever) but BTC net negative in OOS (-11.2%). ETH carries 110% of OOS PnL. Not seed-validated.

**OOS cutoff**: 2025-03-24

## Results

| Period | Sharpe | WR | PF | MaxDD | Trades | PnL |
|--------|--------|-----|------|-------|--------|------|
| IS | +1.32 | 42.6% | 1.27 | 55.3% | 564 | +335% |
| OOS | +1.66 | 45.3% | 1.38 | 30.8% | 137 | +110% |

**Per-symbol IS**: BTC 232 trades (+168%, 50.1%), ETH 332 (+167%, 49.9%) — perfectly balanced
**Per-symbol OOS**: ETH 76 trades, 50.0% WR (+121%, 110.2%), BTC 61 trades, 39.3% WR (-11%, -10.2%) — BTC net negative

## What Happened

Re-ran balanced class weights from iter 048 (which got OOS +0.10). This run got OOS +1.66 — significantly better. However:

1. **BTC is net negative in OOS** (-11.2%): all OOS profit comes from ETH
2. **Not seed-validated**: single seed=42 result. Iter 048 with same approach got OOS +0.10. This suggests high seed sensitivity
3. **IS MaxDD improved**: 55.3% vs baseline 64.3% — class weight balancing does stabilize IS

The IS metrics (Sharpe 1.32, both symbols contributing equally) suggest the balanced-weight approach has merit. But the OOS divergence between BTC (-11%) and ETH (+121%) indicates the model's BTC predictions degrade OOS.

## Decision: NO-MERGE

Despite headline OOS Sharpe +1.66, the single-symbol dependence (ETH = 110% of OOS PnL) and lack of seed validation make this unreliable. Iter 048 with the same approach got OOS +0.10 — the variance is too high.

## Key Insight

Balanced class weights improve IS consistency (lower MaxDD, more balanced per-symbol contribution). The OOS improvement may be real but needs seed validation. Worth revisiting with multi-seed testing.

## Exploration/Exploitation Tracker

Last 10: [..., X, E, E] (E=explore, X=exploit)
Type: EXPLORATION (balanced class weights = structural change to training)

## Next Iteration Ideas

- **Seed-validate iter 050 config**: Run 5 seeds to see if OOS +1.66 is real or lucky
- Try 14-day timeout (timeout trades have 69.6% WR — capturing them could help)
- Independent pair tests: BNB+LINK, AVAX+DOT
