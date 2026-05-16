# Phase 7.5 Critic Review — iter-v3/032

OVERALL: **EXPLORATION-PROMISING-OOS-MIXED** — per-symbol ATR multipliers for LDO works structurally (LDO -3.07 → +3.98 OOS, +6.05 swing); OOS Sharpe +1.93 highest single-seed in v3 catalog; bundle OOS trades 129 at 130 floor; concentration improved. BUT IS Sharpe collapsed -0.56 (same single-seed-lottery pattern as iter-v3/026/027/030).

## Per-Check Status

All 12 methodology checks PASS or PASS-EXPLORATION. BCH/TRX/ALGO bit-identical to iter-v3/029 (per-symbol Optuna independence confirmed; only LDO changed).

## Methodology Innovation — Per-Symbol Labels Validated

iter-v3/030 falsified per-symbol FEATURES for LDO (LDO got worse).
iter-v3/032 validated per-symbol LABELS for LDO (LDO got better).

The hypothesis was: "LDO is regime-mismatched (1.35× peer volatility) → ATR (2.0, 1.0) over-fits LDO → tighter (1.5, 0.75) better fits LDO's volatility profile." Confirmed by EDA (LDO median NATR 5.0 vs peer 3.7) and result (LDO OOS +3.98 vs -3.07 anchor).

This validates the **per-symbol labels methodology** and confirms the deeper insight: when a symbol underperforms, the fix is at the LABELING layer (regime mismatch), not feature layer (feature signature mismatch).

## §4.4 PATH Disposition

| Condition | Anchor (iter-v3/029) | Observed | Status |
|---|---|---|---|
| LDO contribution OOS | -3.07 | +3.98 | ✓ improved |
| BCH/TRX/ALGO bit-identical | yes | yes | ✓ confirmed |
| OOS Sharpe lifted | — | +0.17 | ✓ |
| IS Sharpe maintained | — | -0.56 | ✗ collapsed |
| Concentration improved | 50.6% | 45.10% | ✓ |
| Bundle OOS ≥ 130 | — | 129 | -1 (basically at floor) |

OOS axis: clean PROMISING. IS axis: NEGATIVE-collapse (single-seed lottery suspect).

**Verdict: EXPLORATION-PROMISING-OOS-MIXED** (sub-class of PROMISING with explicit IS caveat).

## Caveats

1. **Single-seed lottery risk**: IS Sharpe collapse to 0.24 with OOS lift to 1.93 is the same pattern as iter-v3/026/027/030 (suspicious IS/OOS divergence). Multi-seed validation at iter-v3/039 is the truth-test.

2. **LDO 20 trades at 35% WR** is statistically modest. Multi-seed will reveal whether the +3.98 OOS lift is robust.

3. **iter-v3/032 IS Sharpe is the lowest in any single-axis EXPLORATION since iter-v3/030**. Combined with iter-v3/030 (IS 0.05) and iter-v3/031 (IS 0.28), the post-iter-v3/029 trajectory shows IS Sharpe degradation from +0.79 → +0.05/+0.28/+0.24 across the LDO experiments. This IS the pattern of single-seed Optuna finding different local minima as the loss surface changes.

## Recommendations to QR

iter-v3/033 axis: **ADD 5TH SYMBOL with per-symbol-feature-signature alignment** methodology (validated at iter-v3/029).

Rationale:
1. Outstanding MERGE gates after iter-v3/032:
   - IS Sharpe +0.24 < +1.0 (gap 0.76) — most aspirational
   - Bundle OOS 129 < 130 (gap 1; trivially closeable)
   - Top-sym 45.1% > 30% (gap 15pp)
2. 5th symbol mechanical lift addresses 2 of 3 gaps simultaneously (bundle trades + concentration)
3. Per-symbol-feature-signature methodology proven at iter-v3/029 (ALGO succeeded where iter-v3/021 HBAR+AVAX failed)
4. Candidates: FILUSDT, VETUSDT, ATOMUSDT — re-evaluate against iter-v3/032 multi-symbol feature importance (4-symbol baseline including ALGO data)

Pre-commits for iter-v3/033:
- ADD chosen 5th symbol to V3_MODELS (4 → 5)
- REQUIRED_GAP 88 → 110
- KEEP all existing edge ingredients (regime_momentum + LDO ATR + 4 symbols)
- Per-symbol feature analysis on 4-symbol baseline (now including ALGO)

Predicted bands:
- IS Sharpe [+0.30, +0.70] median +0.50
- OOS Sharpe [+1.50, +2.10] median +1.80
- Concentration drops to <40%
- Bundle OOS trades > 130

## Catalog Row

`| iter-v3/032 | 2026-05-08 | Per-symbol ATR multipliers for LDO (1.5, 0.75) — LABELING-layer fix; restore LDO V3_MODELS 3→4 | -0.56 (vs iter-v3/029 anchor +0.7926) | +1.9338 (Δ +0.17 — HIGHEST single-seed OOS in v3 catalog; LDO OOS +3.98 vs -3.07 anchor +6.05 swing; bundle 129 at 130 floor) | EXPLORATION-PROMISING-OOS-MIXED | YES — bundle ingredient candidate (regime_momentum + ALGO + LDO_ATR triple validated single-seed); IS Sharpe single-seed collapse caveat carries forward; multi-seed truth-test at iter-v3/039 CONFIRMATION |`
