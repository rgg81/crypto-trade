# MN4 REVEAL LEDGER — append-only; single-use tokens (TOURNAMENT-CHARTER-MN4.md)

One holdout reveal per construction, EVER, on the sealed window `[2024-07-01, 2026-07-01)`. Every
sanctioned holdout access records a `SPENT token=...` line below. NEVER edit or delete existing
lines — this file is the audit record. (Consolidated by the orchestrator from the per-token markers
in `data/mn4_reveal/spend_MN4-NN.json` written atomically by each pair; race-free.)

## Spends — Phase B (all 10 revealed 2026-07-12)

| Token | Idea | Result | Holdout Sharpe 2× | Holdout maxDD |
|---|---|---|---|---|
| `MN4-01` | TS-Momentum (blue-chip, vol-scaled, β-hedged) | FAIL (t-stat gate only; alpha held) | +0.972 | −26.4% |
| `MN4-02` | Meta-Labeled Breakout | FAIL (maxDD + per-half; partial generalizer, crash-fragile) | +0.151 | −33.0% |
| `MN4-03` | Regime-Adaptive Allocator | FAIL (mania-β gate only; alpha held, crisis defense worked) | +0.924 | −39.1% |
| `MN4-04` | Slow ML Factor (flagship) | FAIL (crash edge INVERTED +33%→−192%; IC held but book inverted) | n/a (flat/brake) | 0% / diag −66% |
| `MN4-05` | Kalman Stat-Arb | FAIL (null deepened) | −4.66 | −48.2% |
| `MN4-06` | Funding-Rate Prediction | **PASS** (self-diagnosed regime artifact — carry-regime flip, not alpha) | +1.130 | −28.4% |
| `MN4-07` | XS Reversal (dispersion-gated) | FAIL (null deepened) | −1.74 | −90.1% |
| `MN4-08` | Vol-Targeted Risk-Parity (directional) | FAIL (inverted; bull-regime luck; chops-bleed) | −0.222 | −82.8% |
| `MN4-09` | Calendar/Seasonality Tilt | FAIL (null confirmed) | −0.466 | −38.4% |
| `MN4-10` | Born-Diverse Ensemble | **PASS** (genuine generalizer — held; robustness-first) | +0.487 | −36.3% |

- SPENT token=MN4-01 window=[2024-07-01,2026-07-01) result=FAIL sh2x=+0.972
- SPENT token=MN4-02 window=[2024-07-01,2026-07-01) result=FAIL sh2x=+0.151
- SPENT token=MN4-03 window=[2024-07-01,2026-07-01) result=FAIL sh2x=+0.924
- SPENT token=MN4-04 window=[2024-07-01,2026-07-01) result=FAIL sh2x=n/a(diag −0.88)
- SPENT token=MN4-05 window=[2024-07-01,2026-07-01) result=FAIL sh2x=−4.66
- SPENT token=MN4-06 window=[2024-07-01,2026-07-01) result=PASS sh2x=+1.130
- SPENT token=MN4-07 window=[2024-07-01,2026-07-01) result=FAIL sh2x=−1.74
- SPENT token=MN4-08 window=[2024-07-01,2026-07-01) result=FAIL sh2x=−0.222
- SPENT token=MN4-09 window=[2024-07-01,2026-07-01) result=FAIL sh2x=−0.466
- SPENT token=MN4-10 window=[2024-07-01,2026-07-01) result=PASS sh2x=+0.487

**All 10 tokens spent irreversibly. Two PASS (06, 10), eight FAIL. Phase C (Critic tournament review) adjudicates which (if either) PASS is a genuine generalizer vs a multiplicity artifact.**
