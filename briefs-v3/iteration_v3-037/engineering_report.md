# Engineering Report — iter-v3/037

## Status: READY-FOR-CRITIC

Wall-clock 0.33h. NEGATIVE — LDO cross_asset_divergence_norm catastrophic (-33 OOS swing).

## Headline Metrics

| Metric | Value | vs iter-v3/035 anchor (-0.1023/+2.8521) |
|--------|-------|------------------------------------------|
| IS Sharpe | -0.1466 | Δ -0.04 |
| OOS Sharpe | +2.2289 | Δ -0.62 |
| LDO OOS PnL | **-29.17 (21.1% WR)** | -33.15 swing from +3.98 |

## Per-Symbol — BCH/TRX/ALGO bit-identical to iter-v3/035; LDO catastrophic

| Symbol | weighted_pnl | Trades | WR | vs iter-v3/035 |
|--------|--------------|--------|-----|----------------|
| BCH | +48.73 | 32 | 50.0% | bit-identical |
| TRX | +29.24 | 46 | 52.2% | bit-identical |
| ALGO | +20.87 | 25 | 40.0% | bit-identical |
| **LDO** | **-29.17** | 19 | **21.1%** | **-33.15 swing** |

## Verdict: EXPLORATION-NEGATIVE

cross_asset_divergence_norm is INERT/HARMFUL for v3 architecture both universally (iter-v3/027) and per-symbol (iter-v3/037). Feature CLOSED.

## Cumulative Pattern Recognition

5 of 5 per-symbol feature additions for non-BCH symbols have FAILED:
- iter-v3/030: LDO subset (drop features) — NEGATIVE
- iter-v3/036: TRX vol_adj_autocorr — NEGATIVE
- iter-v3/037: LDO cross_asset_divergence_norm — NEGATIVE

Only successful per-symbol modifications:
- iter-v3/032: LDO per-symbol ATR (LABELS, not features) — VALIDATED
- iter-v3/035: BCH per-symbol fracdiff (FEATURES) — VALIDATED

**Per-symbol additions are HIGHLY SYMBOL-SPECIFIC**. Most candidate features fail when applied per-symbol. Only specific feature-symbol pairs work (fracdiff fits BCH's memory persistence regime; ATR (1.5, 0.75) fits LDO's volatility regime).

## Recommendations

iter-v3/038 (FINAL EXPLORATION): REVERT LDO cross_asset_divergence + ADD ALGO-only fracdiff.

Rationale:
- Tests fracdiff specificity: BCH-only or broadly useful?
- ALGO has +20.87 OOS / 40% WR — improvement room
- If ALGO benefits → may revisit universal fracdiff for iter-v3/039+
- If ALGO doesn't benefit → fracdiff is BCH-specific (further evidence per-symbol features are highly specific)

State after iter-v3/038:
- BCH: 14 + fracdiff (15 features)
- ALGO: 14 + fracdiff (15 features) — if validated, becomes bundle component
- LDO: 14 base
- TRX: 14 base

Status: READY-FOR-CRITIC.
