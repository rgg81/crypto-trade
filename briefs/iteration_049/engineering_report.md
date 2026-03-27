# Engineering Report: Iteration 049

## Configuration

- **Change**: Parallel independent models — BTC+ETH pair + SOL+DOGE pair
- **Symbols**: BTCUSDT, ETHUSDT (pair 1); SOLUSDT, DOGEUSDT (pair 2)
- **Training**: 24 months, 5 CV folds, 50 Optuna trials
- **Barriers**: TP=8%, SL=4%, timeout=7 days (10080 min)
- **Confidence threshold**: Optuna 0.50–0.85
- **Seed**: 42

## Architecture

Each pair gets its own independent LightGBM model. Features generated per-pair, training per-pair, predictions per-pair. Combined trade list sorted by close_time for unified reporting.

## Results

| Metric | IS | OOS | Ratio |
|--------|-----|-----|-------|
| Sharpe | +1.37 | +1.16 | 0.85 |
| WR | 40.9% | 44.9% | 1.10 |
| PF | 1.20 | 1.27 | 1.06 |
| MaxDD | 64.3% | 75.9% | 1.18 |
| Trades | 959 | 136 | — |
| PnL | +445% | +79% | — |

## Per-Symbol Breakdown (IS)

| Symbol | Trades | WR | PnL | % of Total |
|--------|--------|-----|------|------------|
| ETHUSDT | 317 | 45.7% | +306% | 68.7% |
| BTCUSDT | 257 | 40.5% | +82% | 18.4% |
| SOLUSDT | 221 | 37.1% | +58% | 13.0% |
| DOGEUSDT | 164 | 37.2% | -0.3% | -0.1% |

## Per-Symbol Breakdown (OOS)

| Symbol | Trades | WR | PnL | % of Total |
|--------|--------|-----|------|------------|
| BTCUSDT | 50 | 56.0% | +55% | 70.5% |
| ETHUSDT | 86 | 38.4% | +23% | 29.5% |

SOL and DOGE generated zero OOS trades — model abstained entirely.

## Findings

1. Independent parallel model architecture works mechanically
2. SOL+DOGE pair fails at 8%/4% barriers: WR below break-even (37%)
3. OOS result is identical to baseline — adding bad symbols doesn't help
