# Engineering Report — iter-v3/042

## Status: READY-FOR-CRITIC

NEGATIVE — universal (1.5, 0.75) labels caused TRX -33 swing while BCH benefited.

## Headline

| Metric | Value | vs iter-v3/040 anchor (+0.79/+1.77) |
|--------|-------|--------------------------------------|
| IS Sharpe | -0.5941 | Δ -1.39 |
| OOS Sharpe | +2.0752 | Δ +0.31 |

## Per-symbol OOS

| Symbol | weighted_pnl | Trades | WR | vs anchor |
|--------|--------------|--------|-----|-----------|
| BCH | **+52.97** | 41 | **51.2%** | +42 swing (universal tighter helps) |
| LDO | +3.98 | 20 | 35.0% | matches iter-v3/032 LDO-only ATR |
| ALGO | +6.59 | 19 | 36.8% | -14 swing |
| **TRX** | **-3.91** | 42 | **33.3%** | **-33 swing** |

## Lesson

Universal labeling changes have HIGHLY DIVERGENT per-symbol effects. Same as universal feature additions (iter-v3/034 universal fracdiff). The (1.5, 0.75) ATR helped LDO + BCH but hurt TRX + ALGO.

Per-symbol customizations work for ONE symbol; trying to apply universally backfires.

## Recommendations

iter-v3/043: REVERT universal ATR (back to (2.0, 1.0)) + add NEW universal engineered feature with different mechanism. Candidates:
- `efficiency_ratio_50` (Kaufman): abs(close - close.shift(50)) / sum(abs(close - close.shift(1))_50) — well-known regime indicator
- `momentum_persistence_5d_10d`: sign(ret_5d) × sign(ret_10d) — multi-horizon trend agreement

Critic prior: efficiency_ratio_50 (Kaufman). Well-trodden in technical analysis; orthogonal mechanism to regime_momentum_signed_5d.

Status: READY-FOR-CRITIC.
