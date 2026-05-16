# Phase 7.5 Critic Review — iter-v3/037

OVERALL: **EXPLORATION-NEGATIVE** — LDO cross_asset_divergence_norm catastrophic (-33 OOS swing). cross_asset_divergence_norm CLOSED universally + per-symbol.

## Per-Symbol Pattern

5 of 5 non-BCH per-symbol feature additions failed. Only working configurations:
- BCH-only fracdiff (FEATURE addition; iter-v3/035)
- LDO ATR (1.5, 0.75) (LABEL change; iter-v3/032)

Per-symbol architecture is highly selective — most candidate pairings don't help.

## Recommendations

iter-v3/038 final EXPLORATION: REVERT LDO + ADD ALGO-only fracdiff. Tests fracdiff specificity.

## Catalog Row

`| iter-v3/037 | 2026-05-08 | LDO cross_asset_divergence_norm via V3_FEATURES_PER_SYMBOL + revert TRX | -0.04 (vs iter-v3/035 -0.10) | +2.2289 (Δ -0.62; LDO -33 swing 21.1% WR) | EXPLORATION-NEGATIVE | NO — cross_asset_divergence universally + per-symbol failed; iter-v3/038 = revert + ALGO-only fracdiff (test specificity) |`
