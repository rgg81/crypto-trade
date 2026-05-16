# Engineering Report — iter-v3/038

## Status: READY-FOR-CRITIC

Final EXPLORATION (10/10). NEGATIVE — ALGO fracdiff confirms fracdiff is BCH-specific.

## Headline Metrics

| Metric | Value | vs iter-v3/035 anchor |
|--------|-------|------------------------|
| IS Sharpe | -0.3568 | Δ -0.26 |
| OOS Sharpe | +2.4444 | Δ -0.41 |
| ALGO OOS | +12.63 / 27 / 37.0% | -8.24 swing |

ALGO model used fracdiff (importance 40) but performance regressed. fracdiff is genuinely BCH-specific.

## Cycle Final Summary (10/10)

3 PROMISING / 7 NEGATIVE:
- iter-v3/029 ADD ALGO: PROMISING (universe expansion methodology validated)
- iter-v3/032 LDO ATR: PROMISING-MIXED (per-symbol labels)
- iter-v3/035 BCH fracdiff: PROMISING-OOS-MIXED (per-symbol features) — BEST RESULT
- iter-v3/030/031/033/034/036/037/038: NEGATIVE

**Per-symbol additions are EXTREMELY symbol-specific**: 6 of 7 candidate pairings failed. Only fracdiff↔BCH and ATR(1.5,0.75)↔LDO are validated.

## Best Validated Bundle for iter-v3/039 CONFIRMATION

- V3_MODELS = (BCH, LDO, TRX, ALGO) — 4 symbols
- V3_FEATURE_COLUMNS_TOP_N = 14 (incl regime_momentum_signed_5d universal)
- V3_FEATURES_PER_SYMBOL = {"BCHUSDT": 14 + fracdiff_d05_close}
- V3_ATR_MULTIPLIERS_PER_SYMBOL = {"LDOUSDT": (1.5, 0.75)}
- REQUIRED_GAP = 88
- Single-seed (iter-v3/035): IS -0.10 / OOS +2.85
- Multi-seed forecast (50% compression): IS ≈ -0.05 / OOS ≈ +1.4 (clears +1.0 OOS floor!)

iter-v3/039 spec: `--seeds 2 --n-trials 35`, ENSEMBLE_SIZE=5, no --exploration. Wall-clock budget ~3-4h.

Status: READY-FOR-CRITIC.
