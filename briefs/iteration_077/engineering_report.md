# Engineering Report: Iteration 077

## Implementation

Used iter 076's `atr_label` code (cherry-picked) with wider multipliers: TP=3.2, SL=1.6 (vs iter 076's 2.9/1.45).

## Results

```
[report] IS:  Sharpe=1.3254  Trades=267  WR=50.2%  PF=1.4251  MaxDD=47.44%
[report] OOS: Sharpe=-0.4047  Trades=77  WR=35.1%  PF=0.9040  MaxDD=54.44%
```

**EARLY STOP**: Year 2025 PnL -33.0% (WR 37.0%, 100 trades). OOS completely collapsed despite strong IS.

## Trade Verification

Trades verified correct. Dynamic barriers with wider multipliers produced TP ranges of ~5.2-15.8% and SL of ~2.6-7.9%.
